#ifndef NOVIN_PYTHON_BRIDGE_H
#define NOVIN_PYTHON_BRIDGE_H

#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 Initializes the embedded Python runtime. Must be called before any other
 NovinPythonBridge APIs. Returns true on success, false otherwise.

 @param pythonHome Optional path to the Python home directory. Pass NULL to
                   rely on environment variables.
 @param pythonPath Optional path to append to sys.path. Pass NULL to skip.
 @return true if initialization succeeded, false otherwise.
 */
bool novin_python_initialize(const char *pythonHome, const char *pythonPath);

/**
 Processes a security assessment request by invoking novin_ai_bridge.

 @param requestJson JSON string describing the request payload.
 @param clientId Identifier for the client; optional (defaults to ios-client).
 @param brandConfigJson Optional brand configuration JSON to initialize the
                        NovinAIBridge singleton the first time it is used.
 @param errorOut Optional pointer that receives an error message when the call
                 fails. Caller must free using novin_python_free_string.
 @return Newly allocated JSON string response on success; NULL on failure.
 */
const char *novin_python_process_request(const char *requestJson,
                                         const char *clientId,
                                         const char *brandConfigJson,
                                         const char **errorOut);

/** Frees strings returned from novin_python_process_request. */
void novin_python_free_string(const char *string);

/** Finalizes the embedded Python runtime. */
void novin_python_finalize(void);

#ifdef __cplusplus
}
#endif

#endif /* NOVIN_PYTHON_BRIDGE_H */

