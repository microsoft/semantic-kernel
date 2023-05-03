.\1_install-reqs.cmd && start cmd.exe /k ".\2_init-backend.cmd %1" & start cmd.exe /k ".\3_init-frontend.cmd %2 %3"
