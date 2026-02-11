#include <algorithm>
#include <cctype>
#include <filesystem>
#include <iostream>
#include <set>
#include <string>

namespace fs = std::filesystem;

enum class MediaType {
    Images,
    Videos
};

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

int main() {
    std::cout << "Choose media type to move:\n";
    std::cout << "1) Images\n";
    std::cout << "2) Videos\n";
    std::cout << "Enter 1 or 2: ";

    std::string choiceInput;
    std::getline(std::cin, choiceInput);

    MediaType selectedType;
    std::string selectedLabel;

    if (choiceInput == "1") {
        selectedType = MediaType::Images;
        selectedLabel = "images";
    } else if (choiceInput == "2") {
        selectedType = MediaType::Videos;
        selectedLabel = "videos";
    } else {
        std::cerr << "Error: Invalid choice. Please run again and choose 1 or 2.\n";
        return 1;
    }

    std::cout << "Enter source folder path: ";
    std::string sourceInput;
    std::getline(std::cin, sourceInput);

    std::cout << "Enter destination folder path: ";
    std::string destinationInput;
    std::getline(std::cin, destinationInput);

    fs::path sourceDir(sourceInput);
    fs::path destinationDir(destinationInput);

    if (!fs::exists(sourceDir) || !fs::is_directory(sourceDir)) {
        std::cerr << "Error: Source path does not exist or is not a directory.\n";
        return 1;
    }

    if (fs::exists(destinationDir) && fs::equivalent(sourceDir, destinationDir)) {
        std::cerr << "Error: Source and destination cannot be the same folder.\n";
        return 1;
    }

    try {
        if (!fs::exists(destinationDir)) {
            fs::create_directories(destinationDir);
        }
    } catch (const fs::filesystem_error& ex) {
        std::cerr << "Error creating destination directory: " << ex.what() << "\n";
        return 1;
    }

    std::uintmax_t movedCount = 0;
    std::uintmax_t skippedCount = 0;

    try {
        fs::recursive_directory_iterator end;
        for (fs::recursive_directory_iterator it(sourceDir, fs::directory_options::skip_permission_denied); it != end; ++it) {
            const fs::path currentPath = it->path();

            if (!it->is_regular_file()) {
                continue;
            }

            if (!isTargetFile(currentPath, selectedType)) {
                continue;
            }

            fs::path finalDestination = getUniqueDestinationPath(destinationDir, currentPath.filename());

            try {
                fs::rename(currentPath, finalDestination);
                ++movedCount;
                std::cout << "Moved: " << currentPath << " -> " << finalDestination << "\n";
            } catch (const fs::filesystem_error&) {
                try {
                    fs::copy_file(currentPath, finalDestination, fs::copy_options::none);
                    fs::remove(currentPath);
                    ++movedCount;
                    std::cout << "Moved (copy+delete): " << currentPath << " -> " << finalDestination << "\n";
                } catch (const fs::filesystem_error& ex) {
                    ++skippedCount;
                    std::cerr << "Skipped: " << currentPath << " (" << ex.what() << ")\n";
                }
            }
        }
    } catch (const fs::filesystem_error& ex) {
        std::cerr << "Traversal error: " << ex.what() << "\n";
        return 1;
    }

    std::cout << "\nDone. " << selectedLabel << " moved: " << movedCount << ", skipped: " << skippedCount << "\n";
    return 0;
}