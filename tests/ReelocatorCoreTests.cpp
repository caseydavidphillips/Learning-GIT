#include "ReelocatorCore.hpp"

#include <filesystem>
#include <chrono>
#include <fstream>
#include <iostream>
#include <string>

namespace fs = std::filesystem;

namespace {

bool expect(bool condition, const std::string& message) {
    if (!condition) {
        std::cerr << "FAIL: " << message << "\n";
        return false;
    }
    return true;
}

bool testToLowerNormalizesCase() {
    return expect(toLower("MiXeD.Ext") == "mixed.ext", "toLower should normalize mixed-case text");
}

bool testIsTargetFileMatchesCaseInsensitiveImageExtension() {
    return expect(isTargetFile("photo.JPEG", MediaType::Images), "JPEG extension should match image media type");
}

bool testIsTargetFileRejectsWrongMediaType() {
    return expect(!isTargetFile("clip.mp4", MediaType::Images), "video extension should not match image media type");
}

bool testGetUniqueDestinationPathAddsNumericSuffix() {
    const auto tick = std::chrono::high_resolution_clock::now().time_since_epoch().count();
    const fs::path tempDir = fs::temp_directory_path() / ("reelocator-tests-" + std::to_string(tick));
    fs::create_directories(tempDir);

    const fs::path original = tempDir / "capture.png";
    const fs::path firstDuplicate = tempDir / "capture_1.png";

    std::ofstream(original.string()).close();
    std::ofstream(firstDuplicate.string()).close();

    const fs::path uniquePath = getUniqueDestinationPath(tempDir, "capture.png");
    const bool ok = expect(uniquePath.filename() == "capture_2.png", "duplicate names should increment numeric suffix");

    fs::remove_all(tempDir);
    return ok;
}

}  // namespace

int main() {
    bool ok = true;

    ok = testToLowerNormalizesCase() && ok;
    ok = testIsTargetFileMatchesCaseInsensitiveImageExtension() && ok;
    ok = testIsTargetFileRejectsWrongMediaType() && ok;
    ok = testGetUniqueDestinationPathAddsNumericSuffix() && ok;

    if (ok) {
        std::cout << "All Reelocator unit tests passed.\n";
        return 0;
    }

    return 1;
}
