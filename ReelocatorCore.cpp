#include "ReelocatorCore.hpp"

#include <algorithm>
#include <cctype>
#include <set>

std::string toLower(std::string value) {
    std::transform(value.begin(), value.end(), value.begin(),
                   [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    return value;
}

bool isTargetFile(const fs::path& filePath, MediaType mediaType) {
    static const std::set<std::string> imageExtensions = {
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif", ".webp", ".heic", ".ico"
    };

    static const std::set<std::string> videoExtensions = {
        ".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm", ".mpeg", ".mpg", ".m4v"
    };

    const std::string ext = toLower(filePath.extension().string());

    if (mediaType == MediaType::Images) {
        return imageExtensions.find(ext) != imageExtensions.end();
    }

    return videoExtensions.find(ext) != videoExtensions.end();
}

fs::path getUniqueDestinationPath(const fs::path& destinationDir, const fs::path& filename) {
    fs::path candidate = destinationDir / filename;
    if (!fs::exists(candidate)) {
        return candidate;
    }

    fs::path stem = filename.stem();
    fs::path extension = filename.extension();

    int counter = 1;
    while (true) {
        fs::path numberedName = stem.string() + "_" + std::to_string(counter) + extension.string();
        candidate = destinationDir / numberedName;
        if (!fs::exists(candidate)) {
            return candidate;
        }
        ++counter;
    }
}
