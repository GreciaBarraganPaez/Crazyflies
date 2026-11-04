# SwarmGesture: launch the four terminals for the 19-drone demo.
# Place this file in the root of the SwarmGesture repository.
# Run it directly or double-click Start-SwarmGesture.cmd.
param(
    [ValidateSet('start', 'ros', 'bridge', 'markers', 'webcam')]
    [string]$Role = 'start',
    [ValidateSet('animations', 'heart', 'static', 'snake', 'snake-player')]
    [string]$FormationMode = 'animations',
    [ValidateSet('physics', 'preview')]
    [string]$SimulationProfile = 'preview',
    [switch]$NoRviz
)

$ErrorActionPreference = 'Stop'
$Distribution = 'SwarmGesture-Ubuntu'
$ProjectRoot = $PSScriptRoot
$SimulationDir = Join-Path $ProjectRoot 'simulation'

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
        throw 'WSLg display configuration is unexpected. Close the windows and try Start-SwarmGesture-Clean.cmd.'
    }
    # A stale socket can exist even when WSLg cannot accept connections.
    & wsl.exe -d $Distribution -- timeout 8 xdpyinfo -display ':0' 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw 'WSLg is not accepting display connections, so RViz cannot open. Stop the project, run wsl --shutdown, then reopen your usual SwarmGesture launcher.'
    }
}

function Run-UbuntuScript([string]$ScriptName) {
    $windowsScript = Join-Path $SimulationDir $ScriptName
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
        $sceneValue = if ($FormationMode -in @('snake','snake-player')) { $FormationMode } else { 'formations' }
        & wsl.exe -d $Distribution -- bash $linuxScript $SimulationProfile $rvizValue $sceneValue
    } else {
        & wsl.exe -d $Distribution -- bash $linuxScript
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Ubuntu script exited with status $LASTEXITCODE" -ForegroundColor Yellow
    }
}

switch ($Role) {
    'start' {
        if ($FormationMode -in @('snake','snake-player') -and $SimulationProfile -ne 'preview') {
            throw 'Snake currently supports only the ideal preview profile.'
        }
        $required = @(
            'simulation\config\crazyflies.yaml',
            'simulation\config\swarmgesture.rviz',
            'simulation\gesture_bridge.py',
            'simulation\heart_animation_bridge.py',
            'simulation\formation_animation_bridge.py',
            'simulation\smooth_animation_bridge.py',
            'simulation\continuous_trajectories.py',
            'simulation\formation_registry.py',
            'simulation\playback_controls.py',
            'simulation\formations\__init__.py',
            'simulation\formations\heart.py',
            'simulation\formations\sine.py',
            'simulation\formations\spiral.py',
            'simulation\formations\moon.py',
            'simulation\formations\helix.py',
            'simulation\runtime\__init__.py',
            'simulation\runtime\playback.py',
            'simulation\runtime\joined_transitions.py',
            'simulation\blended_transitions.py',
            'simulation\choreography_preview.launch.py',
            'simulation\preview_server.py',
            'simulation\drone_markers.py',
            'simulation\formation_colors.py',
            'simulation\start_ros.sh',
            'simulation\start_bridge.sh',
            'simulation\start_markers.sh',
            'gesture_sender.py',
            'hand_steering.py',
            'models\gesture_svm_mirrored.joblib'
        )
        if ($FormationMode -eq 'snake') {
            $required += @('simulation\snake_controller.py','simulation\snake_preview_server.py',
                'simulation\snake_markers.py','simulation\start_snake_markers.sh',
                'simulation\runtime\snake_scene.py','simulation\scenes\snake.py',
                'simulation\scenes\__init__.py','simulation\scenes\snake_routes.py','simulation\scenes\trajectories.py','simulation\config\snake-smooth.rviz')
        }
        if ($FormationMode -eq 'snake-player') {
            $required += @('simulation\play_snake_controller.py','simulation\play_snake_server.py','simulation\play_snake_markers.py',
                'simulation\scenes\play_snake.py','simulation\runtime\play_snake.py',
                'simulation\config\snake-player.yaml','simulation\config\snake-player.rviz','simulation\start_play_snake_markers.sh')
        }
        foreach ($relativePath in $required) {
            $fullPath = Join-Path $ProjectRoot $relativePath
            if (-not (Test-Path -LiteralPath $fullPath)) {
                Write-Host "Missing file: $fullPath" -ForegroundColor Red
                Write-Host 'Place the launcher files in the repository root and check your existing project files.'
                exit 1
            }
        }
        if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
            Write-Host 'wsl.exe not found on PATH.' -ForegroundColor Red
            exit 1
        }

        $fleetCount = if ($FormationMode -eq 'snake-player') { 8 } else { 19 }
        Write-Host "Starting SwarmGesture ($fleetCount drones, formation mode=$FormationMode, profile=$SimulationProfile, simulation only)..."
        Test-WSLg
        & wsl.exe -d $Distribution -- pgrep -f '^(/usr/bin/python3 /opt/ros/jazzy/lib/crazyflie_sim/crazyflie_server|/usr/bin/python3 .*/(preview_server|snake_preview_server|play_snake_server)\.py)( |$)' | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host 'SwarmGesture is already running. Reuse the open terminals.' -ForegroundColor Yellow
            Write-Host 'For a full restart: land, stop the bridge, then stop ROS, markers and webcam before launching again.'
            Write-Host 'For a controller-only restart: land, stop the bridge, then use Restart-SwarmGesture-Bridge.cmd.'
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
        $fleetCount = if ($FormationMode -eq 'snake-player') { 8 } else { 19 }
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
        if ($FormationMode -eq 'snake') {
            Write-Host 'Autonomous grid Snake: one=takeoff; peace/three/OK=start; fist=grid; palm=land.' -ForegroundColor Cyan
            Write-Host 'Keyboard: snake=start; grid; count 3..15 or seed INTEGER while grounded; status.' -ForegroundColor Cyan
        }
        if ($FormationMode -eq 'snake-player') {
            Write-Host 'Hand Snake: 8 drones, one snake. Peace=start; point one finger and move hand left/right/up/down.' -ForegroundColor Cyan
            Write-Host 'Fist=grid; palm=land. Steer early: smooth turns are planned ahead.' -ForegroundColor Cyan
        }
        Run-UbuntuScript 'start_bridge.sh'
    }
    'markers' {
        $Host.UI.RawUI.WindowTitle = 'SwarmGesture 3 - Colored Drones'
        Write-Host 'Publishing pose-synchronized animated colors to RViz.' -ForegroundColor Cyan
        if ($FormationMode -eq 'snake-player') { Run-UbuntuScript 'start_play_snake_markers.sh' }
        elseif ($FormationMode -eq 'snake') { Run-UbuntuScript 'start_snake_markers.sh' }
        else { Run-UbuntuScript 'start_markers.sh' }
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
        $senderArgs = @('.\gesture_sender.py','--model','models/gesture_svm_mirrored.joblib','--send','--host',$WSL_IP)
        if ($FormationMode -eq 'snake-player') { $senderArgs += '--snake-player' }
        & python @senderArgs
        if ($LASTEXITCODE -ne 0) {
            Write-Host 'Webcam exited with an error; inspect the lines above.' -ForegroundColor Yellow
        }
    }
}
