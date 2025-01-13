# this wrapping script provides Azure authencation before calling actual WARA scripts
Param(
  [ValidatePattern('^(\/subscriptions\/)?[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')]
  [String[]]$SubscriptionIds,
  [GUID]$TenantID
)

Connect-AzAccount
& "$PSScriptRoot\temp_wara_exec\1_wara_collector.ps1" -tenantid $TenantID -subscriptionids $SubscriptionIds

# Connect-AzAccount -Identity
# & "$PSScriptRoot\temp_wara_exec\1_wara_collector.ps1" -tenantid $TenantID -subscriptionids $SubscriptionIds


