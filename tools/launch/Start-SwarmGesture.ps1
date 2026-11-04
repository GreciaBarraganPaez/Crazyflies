# SwarmGesture: launch the four terminals for the 19-drone demo.
# Shared launcher internals; root shortcuts select normal startup or the tools menu.
param(
    [ValidateSet('start', 'ros', 'bridge', 'markers', 'webcam', 'menu')]
    [string]$Role = 'start',
    [ValidateSet('animations', 'heart', 'static')]
    [string]$FormationMode = 'animations',
    [ValidateSet('physics', 'preview')]
    [string]$SimulationProfile = 'preview',
    [switch]$NoRviz
)

$ErrorActionPreference = 'Stop'
$Distribution = 'SwarmGesture-Ubuntu'
$ProjectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$SimulationDir = Join-Path $ProjectRoot 'simulation'
$SimulationLaunchDir = Join-Path $SimulationDir 'launch'

function Launch-Window([string]$WindowRole) {
    # Start-Process needs explicit double quotes around a -File path containing spaces.
    $arguments = '-NoExit -NoProfile -ExecutionPolicy Bypass -File "{0}" -Role {1} -FormationMode {2} -SimulationProfile {3}' -f $PSCommandPath, $WindowRole, $FormationMode, $SimulationProfile
    if ($NoRviz) { $arguments += ' -NoRviz' }
    Start-Process -FilePath 'powershell.exe' -ArgumentList $arguments -WorkingDirectory $ProjectRoot | Out-Null
}

function Test-WSLg {
    # Initializing a distro alone doesn't guarantee its GUI server is healthy.
    $displayValue = & wsl.exe -d $Distribution -- printenv DISPLAY
    $displayStatus = $LASTEXITCODE
    & wsl.exe -d $Distribution -- test -S /tmp/.X11-unix/X0
    $socketStatus = $LASTEXITCODE
    if ($displayStatus -ne 0) { $displayValue = '<unset>' }
    Write-Host "WSLg: DISPLAY=$displayValue; X11 socket exit status=$socketStatus (0 means ready)"
    if (($socketStatus -ne 0) -or ($displayValue -ne ':0')) {
        throw 'WSLg display configuration is unexpected. Close the windows and use WSL recovery in SwarmGesture-Tools.cmd.'
    }
    # A stale socket can exist even when WSLg cannot accept connections.
    & wsl.exe -d $Distribution -- timeout 8 xdpyinfo -display ':0' 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw 'WSLg is not accepting display connections, so RViz cannot open. Stop the project, run wsl --shutdown, then reopen your usual SwarmGesture launcher.'
    }
}

function Run-UbuntuScript([string]$ScriptName) {
    $windowsScript = Join-Path $SimulationLaunchDir $ScriptName
    if (-not (Test-Path -LiteralPath $windowsScript)) {
        throw "Missing file: $windowsScript"
    }

    # Convert C:\... to /mnt/c/...; handles spaces in the repo path.
    $convertedPath = & wsl.exe -d $Distribution -- wslpath -a $windowsScript
    if ($LASTEXITCODE -ne 0 -or -not $convertedPath) {
        throw "Could not convert the path to WSL: $windowsScript"
    }
    $linuxScript = ($convertedPath | Select-Object -Last 1).Trim()
    if ($ScriptName -eq 'start_bridge.sh') {
        & wsl.exe -d $Distribution -- bash $linuxScript $FormationMode
    } elseif ($ScriptName -eq 'start_ros.sh') {
        $rvizValue = if ($NoRviz) { 'False' } else { 'True' }
        $sceneValue = 'formations'
        & wsl.exe -d $Distribution -- bash $linuxScript $SimulationProfile $rvizValue $sceneValue
    } else {
        & wsl.exe -d $Distribution -- bash $linuxScript
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Ubuntu script exited with status $LASTEXITCODE" -ForegroundColor Yellow
    }
}

switch ($Role) {
    'menu' {
        Write-Host '1. Formations   2. Physics   3. Restart stopped bridge   4. WSL recovery   0. Exit'
        $selection = Read-Host 'Choose an option'
        switch ($selection) {
            '1' { & $PSCommandPath -Role start }
            '2' { & $PSCommandPath -Role start -SimulationProfile physics }
            '3' { Write-Host 'Land and stop the old bridge first.'; Launch-Window 'bridge' }
            '4' { & (Join-Path $PSScriptRoot 'Start-SwarmGesture-Clean.cmd') }
            '0' { return }
        }
    }
    'start' {
        $required = @(
            'simulation\config\crazyflies.yaml',
            'simulation\config\swarmgesture.rviz',
            'simulation\controllers\gesture_bridge.py',
            'simulation\controllers\heart_animation_bridge.py',
            'simulation\controllers\formation_animation_bridge.py',
            'simulation\controllers\smooth_animation_bridge.py',
            'simulation\core\continuous_trajectories.py',
            'simulation\core\formation_registry.py',
            'simulation\core\playback_controls.py',
            'simulation\formations\__init__.py',
            'simulation\formations\heart.py',
            'simulation\formations\sine.py',
            'simulation\formations\spiral.py',
            'simulation\formations\moon.py',
            'simulation\formations\helix.py',
            'simulation\runtime\__init__.py',
            'simulation\runtime\playback.py',
            'simulation\runtime\joined_transitions.py',
            'simulation\core\blended_transitions.py',
            'simulation\launch\choreography_preview.launch.py',
            'simulation\servers\preview_server.py',
            'simulation\visualization\drone_markers.py',
            'simulation\visualization\formation_colors.py',
            'simulation\launch\start_ros.sh',
            'simulation\launch\start_bridge.sh',
            'simulation\launch\start_markers.sh',
            'app\gesture_sender.py',
            'app\gesture_features.py',
            'app\gesture_gate.py',
            'models\hand_landmarker.task',
            'models\gesture_svm_mirrored.joblib'
        )
        foreach ($relativePath in $required) {
            $fullPath = Join-Path $ProjectRoot $relativePath
            if (-not (Test-Path -LiteralPath $fullPath)) {
                Write-Host "Missing file: $fullPath" -ForegroundColor Red
                Write-Host 'Keep the project folder layout intact and check the missing file above.'
                exit 1
            }
        }
        if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
            Write-Host 'wsl.exe not found on PATH.' -ForegroundColor Red
            exit 1
        }

        $fleetCount = 19
        Write-Host "Starting SwarmGesture ($fleetCount drones, formation mode=$FormationMode, profile=$SimulationProfile, simulation only)..."
        Test-WSLg
        & wsl.exe -d $Distribution -- pgrep -f '^(/usr/bin/python3 /opt/ros/jazzy/lib/crazyflie_sim/crazyflie_server|/usr/bin/python3 .*/(preview_server|snake_preview_server|play_snake_server)\.py|(/usr/bin/python3|python3) -m simulation\.servers\.(preview_server|snake_preview_server|play_snake_server))( |$)' | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host 'SwarmGesture is already running. Reuse the open terminals.' -ForegroundColor Yellow
            Write-Host 'For a full restart: land, stop the bridge, then stop ROS, markers and webcam before launching again.'
            Write-Host 'For a controller-only restart: land, stop the bridge, then use bridge restart in SwarmGesture-Tools.cmd.'
            return
        }
        Launch-Window 'ros'
        Start-Sleep -Seconds 12  # Cold-start ROS and WSLg can need longer than 6 seconds.
        Launch-Window 'bridge'
        Start-Sleep -Seconds 2
        Launch-Window 'markers'
        Start-Sleep -Seconds 2
        Launch-Window 'webcam'
        Write-Host 'Opened four terminals.'
        Write-Host "1. In the BRIDGE terminal, wait for 'Listening on UDP' and enter: a"
        Write-Host '2. Click the webcam window and press E to enable gesture sending.'
        Write-Host '3. Use x + Enter in the bridge terminal to land. Ctrl+C stops each program.'
    }
    'ros' {
        $Host.UI.RawUI.WindowTitle = "SwarmGesture 1 - ROS + RViz ($SimulationProfile)"
        $fleetCount = 19
        Write-Host "ROS + RViz ($fleetCount simulated drones), profile=$SimulationProfile" -ForegroundColor Cyan
        Run-UbuntuScript 'start_ros.sh'
    }
    'bridge' {
        $Host.UI.RawUI.WindowTitle = "SwarmGesture 2 - Gesture Bridge ($FormationMode)"
        Write-Host "Formation mode: $FormationMode (animations = heart + sine + spiral + moon + 3D helix; heart = heart only; static = all static)." -ForegroundColor Cyan
        Write-Host "When 'Listening on UDP' appears, type a and press Enter." -ForegroundColor Cyan
        Write-Host 'Use x + Enter to return to grid and land.' -ForegroundColor Cyan
        if ($FormationMode -eq 'animations') {
            Write-Host 'Preview: speed 0.5..1.25 while grounded; moon, helix or demo / demo off after takeoff; status.' -ForegroundColor Cyan
        }
        Run-UbuntuScript 'start_bridge.sh'
    }
    'markers' {
        $Host.UI.RawUI.WindowTitle = 'SwarmGesture 3 - Colored Drones'
        Write-Host 'Publishing pose-synchronized animated colors to RViz.' -ForegroundColor Cyan
        Run-UbuntuScript 'start_markers.sh'
    }
    'webcam' {
        $Host.UI.RawUI.WindowTitle = 'SwarmGesture 4 - Webcam'
        Set-Location -LiteralPath $ProjectRoot
        $ipOutput = & wsl.exe -d $Distribution -- hostname -I
        if ($LASTEXITCODE -ne 0) {
            throw 'Could not retrieve the current WSL IP address.'
        }
        $ipv4 = @(($ipOutput -split '\s+') | Where-Object { $_ -match '^\d{1,3}(\.\d{1,3}){3}$' })
        if ($ipv4.Count -eq 0) {
            throw "No IPv4 address found in WSL output: $ipOutput"
        }
        $WSL_IP = $ipv4[0]
        Write-Host "Sending to WSL at $WSL_IP" -ForegroundColor Cyan
        Write-Host 'Click inside the camera window and press E to enable sending.' -ForegroundColor Cyan
        $senderArgs = @('-m','app.gesture_sender','--model','models/gesture_svm_mirrored.joblib','--send','--host',$WSL_IP)
        & python @senderArgs
        if ($LASTEXITCODE -ne 0) {
            Write-Host 'Webcam exited with an error; inspect the lines above.' -ForegroundColor Yellow
        }
    }
}
