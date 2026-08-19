$port = 8080
$folder = "C:\Users\jl_rb\Documents\antigravity\intelligent-chandrasekhar\street_dna"
$listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Any, $port)
$listener.Start()
Write-Host "TCP Web Server started on port $port"

try {
    while ($true) {
        $client = $listener.AcceptTcpClient()
        [System.Threading.Tasks.Task]::Run({
            param($client, $folder)
            try {
                $stream = $client.GetStream()
                $reader = [System.IO.StreamReader]::new($stream, [System.Text.Encoding]::UTF8)
                $firstLine = $reader.ReadLine()
                if ([string]::IsNullOrEmpty($firstLine)) {
                    $client.Close()
                    return
                }

                $parts = $firstLine.Split(" ")
                $path = if ($parts.Length -gt 1) { $parts[1].Split("?")[0] } else { "/index.html" }
                if ($path -eq "/" -or $path -eq "") { $path = "/index.html" }
                
                $localPath = Join-Path $folder ($path.TrimStart('/').Replace('/', '\'))

                if (Test-Path $localPath -PathType Leaf) {
                    $ext = [System.IO.Path]::GetExtension($localPath).ToLower()
                    $mime = switch ($ext) {
                        ".html" { "text/html; charset=utf-8" }
                        ".js"   { "application/javascript; charset=utf-8" }
                        ".css"  { "text/css; charset=utf-8" }
                        ".json" { "application/json; charset=utf-8" }
                        ".geojson" { "application/geo+json; charset=utf-8" }
                        ".png"  { "image/png" }
                        ".jpg"  { "image/jpeg" }
                        default { "application/octet-stream" }
                    }
                    $bytes = [System.IO.File]::ReadAllBytes($localPath)
                    $header = "HTTP/1.1 200 OK`r`nContent-Type: $mime`r`nContent-Length: $($bytes.Length)`r`nAccess-Control-Allow-Origin: *`r`nConnection: close`r`n`r`n"
                    $headerBytes = [System.Text.Encoding]::UTF8.GetBytes($header)
                    $stream.Write($headerBytes, 0, $headerBytes.Length)
                    $stream.Write($bytes, 0, $bytes.Length)
                } else {
                    $msg = [System.Text.Encoding]::UTF8.GetBytes("404 Not Found: $path")
                    $header = "HTTP/1.1 404 Not Found`r`nContent-Type: text/plain`r`nContent-Length: $($msg.Length)`r`nConnection: close`r`n`r`n"
                    $headerBytes = [System.Text.Encoding]::UTF8.GetBytes($header)
                    $stream.Write($headerBytes, 0, $headerBytes.Length)
                    $stream.Write($msg, 0, $msg.Length)
                }
                $stream.Flush()
            } catch {}
            finally {
                $client.Close()
            }
        }.GetNewClosure(), @($client, $folder)) | Out-Null
    }
} finally {
    $listener.Stop()
}
