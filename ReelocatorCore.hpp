#pragma once

#include <filesystem>
#include <string>

namespace fs = std::filesystem;

enum class MediaType {
    Images,
    Videos
};

std::string toLower(std::string value);
bool isTargetFile(const fs::path& filePath, MediaType mediaType);
fs::path getUniqueDestinationPath(const fs::path& destinationDir, const fs::path& filename);

