param(
    [ValidateSet("Hourly", "Daily", "Weekly", "Monthly")]
    [string]$Frequency = "Weekly",

    [string]$DaysOfWeek = "Monday",

    [string]$At = "6:00AM",

    [int]$IntervalMinutes = 60,

    [int]$RepetitionDurationHours = 24,

    [string]$TaskName = "ScholarSiteScraper"
)
#Create the scheduled task action to run the scraper.py script using Python
$batchDir = Split-Path -Parent $PSCommandPath
$scriptPath = Join-Path $batchDir "scraper.py"
$command = "cd /d `"$batchDir`" && py -3 `"$scriptPath`""
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c $command"

switch ($Frequency) {
    "Hourly" {
        # Use a single start time with repetition rather than a daily trigger.
        $trigger = New-ScheduledTaskTrigger -Once -At $At -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) -RepetitionDuration (New-TimeSpan -Hours $RepetitionDurationHours)
    }
    "Daily" {
        if ($IntervalMinutes -gt 0) {
            $trigger = New-ScheduledTaskTrigger -Daily -At $At -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) -RepetitionDuration (New-TimeSpan -Hours $RepetitionDurationHours)
        } else {
            $trigger = New-ScheduledTaskTrigger -Daily -At $At
        }
    }
    "Weekly" {
        $days = $DaysOfWeek -split '[, ]+' | Where-Object { $_ }
        if ($IntervalMinutes -gt 0) {
            $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $days -At $At -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) -RepetitionDuration (New-TimeSpan -Hours $RepetitionDurationHours)
        } else {
            $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $days -At $At
        }
    }
    "Monthly" {
        if ($IntervalMinutes -gt 0) {
            $trigger = New-ScheduledTaskTrigger -Monthly -At $At -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) -RepetitionDuration (New-TimeSpan -Hours $RepetitionDurationHours)
        } else {
            $trigger = New-ScheduledTaskTrigger -Monthly -At $At
        }
    }
}

if (-not $trigger) {
    throw "Failed to create a scheduled task trigger for frequency '$Frequency'."
}

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Write-Host "Updating existing scheduled task '$TaskName'..."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

$taskParams = @{
    TaskName    = $TaskName
    Action      = $action
    Trigger     = $trigger
    Description = "Run ScholarSite scraper from $scriptPath"
}

if (([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    $taskParams["RunLevel"] = "Highest"
} else {
    Write-Host "Not running as administrator; creating task without elevated run level."
}

Register-ScheduledTask @taskParams

Write-Host "Scheduled task '$TaskName' created successfully."
Write-Host "Frequency: $Frequency"
Write-Host "Interval: $IntervalMinutes minutes"
Write-Host "Duration: $RepetitionDurationHours hours"
if ($Frequency -eq "Weekly") {
    Write-Host "Trigger: $DaysOfWeek at $At"
} else {
    Write-Host "Trigger: $At"
}
