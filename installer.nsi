; installer.nsi — NSIS installer for UglyPDF
; Build with: makensis installer.nsi
; Requires dist\UglyPDF\ to already exist (run build.bat first).

!include "MUI2.nsh"

; ---------------------------------------------------------------------------
; Constants — bump APP_VERSION alongside app/tab_about.py::VERSION
; ---------------------------------------------------------------------------
!define APP_NAME        "UglyPDF"
!define APP_VERSION      "1.0.2"
!define APP_PUBLISHER    "okik4zuya"
!define APP_EXE          "UglyPDF.exe"
!define APP_URL          "https://github.com/okik4zuya/uglypdf"
!define UNINSTALL_KEY    "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"

Name "${APP_NAME}"
OutFile "dist\UglyPDFSetup-${APP_VERSION}.exe"
InstallDir "$PROGRAMFILES64\${APP_NAME}"
InstallDirRegKey HKLM "Software\${APP_NAME}" "InstallDir"
RequestExecutionLevel admin

!define MUI_ABORTWARNING
!define MUI_ICON "icon.ico"
!define MUI_UNICON "icon.ico"

; ---------------------------------------------------------------------------
; Pages
; ---------------------------------------------------------------------------
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
Page custom DesktopShortcutPageCreate DesktopShortcutPageLeave
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

; ---------------------------------------------------------------------------
; Desktop shortcut checkbox (simple custom page)
; ---------------------------------------------------------------------------
Var Dialog
Var DesktopCheckbox
Var CreateDesktopShortcut

Function DesktopShortcutPageCreate
    !insertmacro MUI_HEADER_TEXT "Additional Shortcuts" "Choose additional shortcuts to create."
    nsDialogs::Create 1018
    Pop $Dialog
    ${If} $Dialog == error
        Abort
    ${EndIf}

    ${NSD_CreateCheckbox} 0 0 100% 12u "Create a Desktop shortcut"
    Pop $DesktopCheckbox
    ${NSD_SetState} $DesktopCheckbox ${BST_CHECKED}

    nsDialogs::Show
FunctionEnd

Function DesktopShortcutPageLeave
    ${NSD_GetState} $DesktopCheckbox $CreateDesktopShortcut
FunctionEnd

!include "nsDialogs.nsh"

; ---------------------------------------------------------------------------
; Install
; ---------------------------------------------------------------------------
Section "Install" SEC01
    SetOutPath "$INSTDIR"
    File /r "dist\UglyPDF\*.*"

    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortcut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"
    CreateShortcut "$SMPROGRAMS\${APP_NAME}\Uninstall ${APP_NAME}.lnk" "$INSTDIR\Uninstall.exe"

    ${If} $CreateDesktopShortcut == ${BST_CHECKED}
        CreateShortcut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"
    ${EndIf}

    WriteRegStr HKLM "Software\${APP_NAME}" "InstallDir" "$INSTDIR"

    WriteRegStr HKLM "${UNINSTALL_KEY}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "${UNINSTALL_KEY}" "DisplayVersion" "${APP_VERSION}"
    WriteRegStr HKLM "${UNINSTALL_KEY}" "Publisher" "${APP_PUBLISHER}"
    WriteRegStr HKLM "${UNINSTALL_KEY}" "DisplayIcon" "$INSTDIR\${APP_EXE}"
    WriteRegStr HKLM "${UNINSTALL_KEY}" "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "${UNINSTALL_KEY}" "QuietUninstallString" '"$INSTDIR\Uninstall.exe" /S'
    WriteRegStr HKLM "${UNINSTALL_KEY}" "InstallLocation" "$INSTDIR"
    WriteRegDWORD HKLM "${UNINSTALL_KEY}" "NoModify" 1
    WriteRegDWORD HKLM "${UNINSTALL_KEY}" "NoRepair" 1

    ; EstimatedSize wants KB
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD HKLM "${UNINSTALL_KEY}" "EstimatedSize" "$0"

    WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

!include "FileFunc.nsh"

; ---------------------------------------------------------------------------
; Uninstall
; ---------------------------------------------------------------------------
Section "Uninstall"
    RMDir /r "$INSTDIR"

    Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_NAME}\Uninstall ${APP_NAME}.lnk"
    RMDir "$SMPROGRAMS\${APP_NAME}"
    Delete "$DESKTOP\${APP_NAME}.lnk"

    DeleteRegKey HKLM "${UNINSTALL_KEY}"
    DeleteRegKey HKLM "Software\${APP_NAME}"
SectionEnd
