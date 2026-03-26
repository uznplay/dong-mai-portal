$resp = Invoke-RestMethod -Uri "http://localhost:5000/scan" -Method POST -InFile "D:\doc3d_dataset\extracted\image\1.jpg" -ContentType "image/jpeg"
$resp | ConvertTo-Json
