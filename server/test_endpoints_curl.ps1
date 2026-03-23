$BASE_URL = "http://127.0.0.1:8001"
$CSV_PATH = "C:\Users\Deepak\OneDrive\Desktop\fraudlenz\data\raw\sample2.csv"
$FILE_ID = "replace-with-file-id-from-clean-csv-response"

Write-Host "Health check"
curl.exe "$BASE_URL/health"

Write-Host ""
Write-Host "Upload CSV for cleaning"
curl.exe -X POST "$BASE_URL/api/v1/clean-csv" `
  -H "accept: application/json" `
  -H "Content-Type: multipart/form-data" `
  -F "file=@$CSV_PATH"

Write-Host ""
Write-Host "Download cleaned CSV"
curl.exe -X GET "$BASE_URL/api/v1/clean-csv/$FILE_ID/download" `
  --output "cleaned_output.csv"
