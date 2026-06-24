; PDF Toolbox Installer Script
; NSIS Installer Configuration

!define PRODUCT_NAME "PDF Toolbox"
!define PRODUCT_VERSION "1.0.0"
!define PRODUCT_PUBLISHER "Your Name"
!define PRODUCT_WEB_SITE "https://github.com/yourusername/pdf-split-tool"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\split_pdf_gui.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"

; MUI Settings
!include "MUI2.nsh"

!define MUI_ABORTWARNING
!define MUI_ICON "icon.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; Welcome page
!insertmacro MUI_PAGE_WELCOME
; License page
!insertmacro MUI_PAGE_LICENSE "LICENSE"
; Directory page
!insertmacro MUI_PAGE_DIRECTORY
; Instfiles page
!insertmacro MUI_PAGE_INSTFILES
; Finish page
!define MUI_FINISHPAGE_RUN "$INSTDIR\split_pdf_gui.exe"
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_INSTFILES

; Language files
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "SimpChinese"

; Installer attributes
Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "PDF_Toolbox_Setup.exe"
InstallDir "$PROGRAMFILES\PDF Toolbox"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show

Section "MainSection" SEC01
  SetOutPath "$INSTDIR"
  SetOverwrite ifnewer
  File "dist\split_pdf_gui.exe"

  ; Create shortcuts
  CreateDirectory "$SMPROGRAMS\PDF Toolbox"
  CreateShortCut "$SMPROGRAMS\PDF Toolbox\PDF Toolbox.lnk" "$INSTDIR\split_pdf_gui.exe"
  CreateShortCut "$DESKTOP\PDF Toolbox.lnk" "$INSTDIR\split_pdf_gui.exe"
SectionEnd

Section -AdditionalIcons
  CreateShortCut "$SMPROGRAMS\PDF Toolbox\Uninstall.lnk" "$INSTDIR\uninst.exe"
SectionEnd

Section -Post
  WriteUninstaller "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\split_pdf_gui.exe"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\split_pdf_gui.exe"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
SectionEnd

Section Uninstall
  Delete "$INSTDIR\split_pdf_gui.exe"
  Delete "$INSTDIR\uninst.exe"

  Delete "$SMPROGRAMS\PDF Toolbox\Uninstall.lnk"
  Delete "$SMPROGRAMS\PDF Toolbox\PDF Toolbox.lnk"
  Delete "$DESKTOP\PDF Toolbox.lnk"

  RMDir "$SMPROGRAMS\PDF Toolbox"
  RMDir "$INSTDIR"

  DeleteRegKey HKLM "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
  SetAutoClose true
SectionEnd
