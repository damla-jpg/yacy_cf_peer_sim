# Make a for loop
for ($i = 30; $i -lt 31; $i++) {
    # Print the current round
    Write-Host "Round $i started. Running main.py with argument 1 0"

    # Run the main script with the argument 10 1
    python "C:\Users\damla\Documents\GitHub\experiments\main.py" 1 0

    Write-Host "Main function finished. Waiting for 10 seconds."

    # Wait for main script to finish
    Start-Sleep -Seconds 5

    # Create a folder in "C:\Users\damla\Documents\GitHub\experiments"
    New-Item -ItemType Directory -Path "C:\Users\damla\Documents\GitHub\experiments\non-local-ip-test\round_$i"

    Write-Host "Folder named round_$i created. Copying files."

    # Copy every folder in the "C:\Users\damla\Documents\GitHub\yacy_cf_peersim\docker" folder to the current folder
    Copy-Item -Path "C:\Users\damla\Documents\GitHub\experiments\docker\*" -Destination "C:\Users\damla\Documents\GitHub\experiments\non-local-ip-test\round_$i" -Recurse

    Write-Host "Files copied. Running clear_folders.py with argument 10"

    # Run clear_folders.py with argument 10
    python "C:\Users\damla\Documents\GitHub\experiments\clear_folders.py" 1
}