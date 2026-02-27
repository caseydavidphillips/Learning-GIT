#include "ReelocatorCore.hpp"

#include <chrono>
#include <filesystem>
#include <functional>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

namespace fs = std::filesystem;

namespace {

enum class TestStatus {
    Passed,
    Failed,
    Skipped,
    Error,
};

struct TestResult {
    std::string name;
    TestStatus status;
    std::string message;
    double timeSeconds;
};

std::string xmlEscape(const std::string& text) {
    std::string escaped;
    escaped.reserve(text.size());

    for (const char ch : text) {
        switch (ch) {
        case '&':
            escaped += "&amp;";
            break;
        case '<':
            escaped += "&lt;";
            break;
        case '>':
            escaped += "&gt;";
            break;
        case '"':
            escaped += "&quot;";
            break;
        case '\'':
            escaped += "&apos;";
            break;
        default:
            escaped += ch;
            break;
        }
    }

    return escaped;
}

bool ensureParentDirectory(const fs::path& outputPath) {
    const fs::path parent = outputPath.parent_path();
    if (parent.empty()) {
        return true;
    }

    std::error_code ec;
    fs::create_directories(parent, ec);
    return !ec;
}

bool writeJUnitReport(const fs::path& outputPath, const std::vector<TestResult>& results) {
    if (!ensureParentDirectory(outputPath)) {
        std::cerr << "Failed to create test report directory: " << outputPath.parent_path() << "\n";
        return false;
    }

    int failures = 0;
    int errors = 0;
    int skipped = 0;
    double totalTime = 0.0;

    for (const TestResult& result : results) {
        totalTime += result.timeSeconds;
        if (result.status == TestStatus::Failed) {
            ++failures;
        } else if (result.status == TestStatus::Error) {
            ++errors;
        } else if (result.status == TestStatus::Skipped) {
            ++skipped;
        }
    }

    std::ofstream out(outputPath);
    if (!out) {
        std::cerr << "Failed to open test report file for writing: " << outputPath << "\n";
        return false;
    }

    out << "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n";
    out << "<testsuite name=\"reelocator-unit-tests\" tests=\"" << results.size()
        << "\" failures=\"" << failures
        << "\" errors=\"" << errors
        << "\" skipped=\"" << skipped
        << "\" time=\"" << totalTime << "\">\n";

    for (const TestResult& result : results) {
        out << "  <testcase classname=\"reelocator\" name=\"" << xmlEscape(result.name)
            << "\" time=\"" << result.timeSeconds << "\"";

        if (result.status == TestStatus::Passed) {
            out << "/>\n";
            continue;
        }

        out << ">\n";
        if (result.status == TestStatus::Failed) {
            out << "    <failure message=\"" << xmlEscape(result.message) << "\"/>\n";
        } else if (result.status == TestStatus::Error) {
            out << "    <error message=\"" << xmlEscape(result.message) << "\"/>\n";
        } else if (result.status == TestStatus::Skipped) {
            out << "    <skipped message=\"" << xmlEscape(result.message) << "\"/>\n";
        }

        out << "  </testcase>\n";
    }

    out << "</testsuite>\n";
    return true;
}

TestResult runTest(const std::string& name, const std::function<std::string()>& testFn) {
    const auto start = std::chrono::steady_clock::now();
    const std::string errorMessage = testFn();
    const auto end = std::chrono::steady_clock::now();

    TestResult result;
    result.name = name;
    result.status = errorMessage.empty() ? TestStatus::Passed : TestStatus::Failed;
    result.message = errorMessage;
    result.timeSeconds = std::chrono::duration<double>(end - start).count();

    return result;
}

std::string testToLowerNormalizesCase() {
    if (toLower("MiXeD.Ext") == "mixed.ext") {
        return "";
    }

    return "toLower should normalize mixed-case text";
}

std::string testIsTargetFileMatchesCaseInsensitiveImageExtension() {
    if (isTargetFile("photo.JPEG", MediaType::Images)) {
        return "";
    }

    return "JPEG extension should match image media type";
}

std::string testIsTargetFileRejectsWrongMediaType() {
    if (!isTargetFile("clip.mp4", MediaType::Images)) {
        return "";
    }

    return "video extension should not match image media type";
}

std::string testGetUniqueDestinationPathAddsNumericSuffix() {
    const auto tick = std::chrono::high_resolution_clock::now().time_since_epoch().count();
    const fs::path tempDir = fs::temp_directory_path() / ("reelocator-tests-" + std::to_string(tick));
    fs::create_directories(tempDir);

    const fs::path original = tempDir / "capture.png";
    const fs::path firstDuplicate = tempDir / "capture_1.png";

    std::ofstream(original.string()).close();
    std::ofstream(firstDuplicate.string()).close();

    const fs::path uniquePath = getUniqueDestinationPath(tempDir, "capture.png");
    const bool ok = uniquePath.filename() == "capture_2.png";

    fs::remove_all(tempDir);

    if (ok) {
        return "";
    }

    return "duplicate names should increment numeric suffix";
}

}  // namespace

int main(int argc, char* argv[]) {
    fs::path junitOutputPath;

    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        if (arg == "--junit-out" && (i + 1) < argc) {
            junitOutputPath = argv[++i];
        }
    }

    std::vector<TestResult> results;
    results.reserve(4);

    results.push_back(runTest("toLower normalizes case", testToLowerNormalizesCase));
    results.push_back(runTest("isTargetFile matches case-insensitive image extension", testIsTargetFileMatchesCaseInsensitiveImageExtension));
    results.push_back(runTest("isTargetFile rejects wrong media type", testIsTargetFileRejectsWrongMediaType));
    results.push_back(runTest("getUniqueDestinationPath adds numeric suffix", testGetUniqueDestinationPathAddsNumericSuffix));

    bool allPassed = true;
    for (const TestResult& result : results) {
        if (result.status == TestStatus::Passed) {
            std::cout << "PASS: " << result.name << "\n";
            continue;
        }

        allPassed = false;
        std::cerr << "FAIL: " << result.name << " - " << result.message << "\n";
    }

    if (!junitOutputPath.empty()) {
        const bool wroteReport = writeJUnitReport(junitOutputPath, results);
        if (!wroteReport) {
            allPassed = false;
        } else {
            std::cout << "JUnit report written to " << junitOutputPath << "\n";
        }
    }

    if (allPassed) {
        std::cout << "All Reelocator unit tests passed.\n";
        return 0;
    }

    return 1;
}
