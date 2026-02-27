#include "ReelocatorCore.hpp"

#include <chrono>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>

namespace fs = std::filesystem;

namespace {

enum class TestStatus {
    Pass,
    Fail,
    Skipped,
    Error,
};

struct TestCaseResult {
    std::string name;
    double durationSeconds;
    TestStatus status;
    std::string message;
};

struct AssertionFailure {
    explicit AssertionFailure(std::string failureMessage) : message(std::move(failureMessage)) {}

    std::string message;
};

struct SkippedTest {
    explicit SkippedTest(std::string skipMessage) : message(std::move(skipMessage)) {}

    std::string message;
};

void expect(bool condition, const std::string& message) {
    if (!condition) {
        throw AssertionFailure(message);
    }
}

std::string statusToString(TestStatus status) {
    switch (status) {
        case TestStatus::Pass:
            return "pass";
        case TestStatus::Fail:
            return "fail";
        case TestStatus::Skipped:
            return "skipped";
        case TestStatus::Error:
            return "error";
    }

    return "error";
}

std::string escapeXml(const std::string& text) {
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
            case '\"':
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

template <typename Func>
TestCaseResult runTestCase(const std::string& name, Func testFunc) {
    const auto start = std::chrono::steady_clock::now();

    TestCaseResult result{name, 0.0, TestStatus::Pass, ""};

    try {
        testFunc();
    } catch (const AssertionFailure& failure) {
        result.status = TestStatus::Fail;
        result.message = failure.message;
    } catch (const SkippedTest& skipped) {
        result.status = TestStatus::Skipped;
        result.message = skipped.message;
    } catch (const std::exception& ex) {
        result.status = TestStatus::Error;
        result.message = ex.what();
    } catch (...) {
        result.status = TestStatus::Error;
        result.message = "Unknown non-standard exception";
    }

    const auto end = std::chrono::steady_clock::now();
    result.durationSeconds = std::chrono::duration<double>(end - start).count();

    return result;
}

void testToLowerNormalizesCase() {
    expect(toLower("MiXeD.Ext") == "mixed.ext", "toLower should normalize mixed-case text");
}

void testIsTargetFileMatchesCaseInsensitiveImageExtension() {
    expect(isTargetFile("photo.JPEG", MediaType::Images), "JPEG extension should match image media type");
}

void testIsTargetFileRejectsWrongMediaType() {
    expect(!isTargetFile("clip.mp4", MediaType::Images), "video extension should not match image media type");
}

void testGetUniqueDestinationPathAddsNumericSuffix() {
    const auto tick = std::chrono::high_resolution_clock::now().time_since_epoch().count();
    const fs::path tempDir = fs::temp_directory_path() / ("reelocator-tests-" + std::to_string(tick));
    fs::create_directories(tempDir);

    const fs::path original = tempDir / "capture.png";
    const fs::path firstDuplicate = tempDir / "capture_1.png";

    std::ofstream(original.string()).close();
    std::ofstream(firstDuplicate.string()).close();

    const fs::path uniquePath = getUniqueDestinationPath(tempDir, "capture.png");
    expect(uniquePath.filename() == "capture_2.png", "duplicate names should increment numeric suffix");

    fs::remove_all(tempDir);
}

fs::path parseJunitOutputPath(int argc, char* argv[]) {
    fs::path outputPath = fs::path("build") / "test-results" / "reelocator-unit.xml";

    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        if (arg == "--junit-out") {
            if (i + 1 >= argc) {
                throw std::invalid_argument("--junit-out requires a path argument");
            }
            outputPath = argv[++i];
            continue;
        }

        throw std::invalid_argument("Unknown argument: " + arg);
    }

    return outputPath;
}

void writeJunitXml(const fs::path& outputPath, const std::vector<TestCaseResult>& results) {
    std::size_t failures = 0;
    std::size_t errors = 0;
    std::size_t skipped = 0;
    double totalTime = 0.0;

    for (const TestCaseResult& result : results) {
        totalTime += result.durationSeconds;
        if (result.status == TestStatus::Fail) {
            ++failures;
        } else if (result.status == TestStatus::Error) {
            ++errors;
        } else if (result.status == TestStatus::Skipped) {
            ++skipped;
        }
    }

    fs::create_directories(outputPath.parent_path());
    std::ofstream out(outputPath);
    if (!out.is_open()) {
        throw std::runtime_error("Failed to open JUnit output path: " + outputPath.string());
    }

    out << "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n";
    out << "<testsuite name=\"reelocator_unit_tests\" tests=\"" << results.size() << "\" failures=\"" << failures
        << "\" errors=\"" << errors << "\" skipped=\"" << skipped << "\" time=\"" << std::fixed
        << std::setprecision(6) << totalTime << "\">\n";

    for (const TestCaseResult& result : results) {
        out << "  <testcase name=\"" << escapeXml(result.name) << "\" time=\"" << std::fixed << std::setprecision(6)
            << result.durationSeconds << "\">\n";

        if (result.status == TestStatus::Fail) {
            out << "    <failure message=\"" << escapeXml(result.message) << "\">" << escapeXml(result.message)
                << "</failure>\n";
        } else if (result.status == TestStatus::Error) {
            out << "    <error message=\"" << escapeXml(result.message) << "\">" << escapeXml(result.message)
                << "</error>\n";
        } else if (result.status == TestStatus::Skipped) {
            out << "    <skipped message=\"" << escapeXml(result.message) << "\"/>\n";
        }

        out << "  </testcase>\n";
    }

    out << "</testsuite>\n";
}

}  // namespace

int main(int argc, char* argv[]) {
    fs::path junitOutputPath;
    try {
        junitOutputPath = parseJunitOutputPath(argc, argv);
    } catch (const std::exception& ex) {
        std::cerr << "Argument error: " << ex.what() << "\n";
        return 2;
    }

    std::vector<TestCaseResult> results;
    results.reserve(4);

    results.push_back(runTestCase("testToLowerNormalizesCase", testToLowerNormalizesCase));
    results.push_back(runTestCase("testIsTargetFileMatchesCaseInsensitiveImageExtension", testIsTargetFileMatchesCaseInsensitiveImageExtension));
    results.push_back(runTestCase("testIsTargetFileRejectsWrongMediaType", testIsTargetFileRejectsWrongMediaType));
    results.push_back(runTestCase("testGetUniqueDestinationPathAddsNumericSuffix", testGetUniqueDestinationPathAddsNumericSuffix));

    bool ok = true;
    for (const TestCaseResult& result : results) {
        std::cout << statusToString(result.status) << ": " << result.name;
        if (!result.message.empty()) {
            std::cout << " - " << result.message;
        }
        std::cout << "\n";

        if (result.status == TestStatus::Fail || result.status == TestStatus::Error) {
            ok = false;
        }
    }

    try {
        writeJunitXml(junitOutputPath, results);
        std::cout << "JUnit XML written to " << junitOutputPath.string() << "\n";
    } catch (const std::exception& ex) {
        std::cerr << "Failed to write JUnit XML: " << ex.what() << "\n";
        return 2;
    }

    if (ok) {
        std::cout << "All Reelocator unit tests passed.\n";
        return 0;
    }

    return 1;
}
