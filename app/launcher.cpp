#define UNICODE
#define _UNICODE
#include <windows.h>
#include <string>

// Double-clicking opens the ImGui window with no console. The launcher only finds the
// private runtime next to itself and hands over to runtime/bootstrap.py, which survives
// application updates and applies a staged one first.
int WINAPI wWinMain(HINSTANCE, HINSTANCE, PWSTR arguments, int) {
    wchar_t buffer[32768];
    GetModuleFileNameW(nullptr, buffer, 32768);
    std::wstring root(buffer);
    root.resize(root.find_last_of(L"\\/"));
    // venv layout (runtime\python\Scripts\pythonw.exe) or portable layout (runtime\python\pythonw.exe)
    std::wstring python = root + L"\\runtime\\python\\Scripts\\pythonw.exe";
    if (GetFileAttributesW(python.c_str()) == INVALID_FILE_ATTRIBUTES) python = root + L"\\runtime\\python\\pythonw.exe";
    std::wstring bootstrap = root + L"\\runtime\\bootstrap.py";
    if (GetFileAttributesW(python.c_str()) == INVALID_FILE_ATTRIBUTES ||
        GetFileAttributesW(bootstrap.c_str()) == INVALID_FILE_ATTRIBUTES) {
        MessageBoxW(nullptr, L"Private runtime missing (runtime\\python or runtime\\bootstrap.py).\n\nSee LISEZ-MOI.md.",
                    L"CyTools Storyboard", MB_ICONERROR);
        return 1;
    }
    std::wstring command = L"\"" + python + L"\" \"" + bootstrap + L"\" " + arguments;
    STARTUPINFOW startup{};
    startup.cb = sizeof(startup);
    PROCESS_INFORMATION process{};
    // Working directory = Tool root, so a launch from any folder behaves the same.
    if (!CreateProcessW(python.c_str(), command.data(), nullptr, nullptr, FALSE, 0, nullptr, root.c_str(),
                        &startup, &process)) {
        MessageBoxW(nullptr, L"Could not start the CyTools Storyboard runtime.", L"CyTools Storyboard", MB_ICONERROR);
        return 2;
    }
    CloseHandle(process.hThread);
    CloseHandle(process.hProcess);
    return 0;
}
