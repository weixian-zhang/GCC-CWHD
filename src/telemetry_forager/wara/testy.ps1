

Connect-AzAccount -Identity
$AzContext = Get-AzContext -ErrorAction SilentlyContinue
$AzContext | ConvertTo-Json


