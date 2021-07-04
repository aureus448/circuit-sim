:: This Document has been prepared by Nate Ruppert (nathaniel.ruppert@sce.com)
:: For help regarding this document / necessary changes, please contact the above individual
:: Note: Please use PyCharm, this script is now provided as an extra option to complete both


:: Disables command info in-prompt
@echo OFF
title Doc Creator

:: Run :)
echo Documentation Generation - v1.1 by Nate Ruppert


echo Making HTML Documentation
echo Note: Ignore warnings that begin with "rinoh"
sphinx-build -j 4 -w build/build_err.txt -b html source build/html
pause

cls
echo Making PDF Documentation
echo Note: Ignore warnings that begin with "rinoh"
sphinx-build -w build/build_err_pdf.txt -b rinoh source build/pdf

cls
echo Done! Any Errors may be checked by looking at the build_err file in docs folder!
echo Please note the errors in scripts take precedence over rST errors
pause
