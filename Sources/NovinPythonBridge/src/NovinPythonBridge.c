#include "NovinPythonBridge.h"

#include <Python.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>

static bool s_pythonInitialized = false;
static PyObject *s_novinBridgeInstance = NULL;
static wchar_t *s_pythonHomeW = NULL;
static wchar_t *s_pythonPathW = NULL;
static PyThreadState *s_mainThreadState = NULL;

static void ensure_bridge_initialized(const char *brandConfigJson) {
    if (s_novinBridgeInstance) {
        return;
    }

    PyObject *moduleName = PyUnicode_FromString("novin_ai_bridge");
    if (!moduleName) {
        PyErr_Print();
        return;
    }

    PyObject *module = PyImport_Import(moduleName);
    Py_DECREF(moduleName);
    if (!module) {
        PyErr_Print();
        return;
    }

    PyObject *class = PyObject_GetAttrString(module, "NovinAIBridge");
    Py_DECREF(module);
    if (!class) {
        PyErr_Print();
        return;
    }

    PyObject *args = NULL;
    if (brandConfigJson && strlen(brandConfigJson) > 0) {
        PyObject *jsonModule = PyImport_ImportModule("json");
        if (jsonModule) {
            PyObject *loadsFunc = PyObject_GetAttrString(jsonModule, "loads");
            Py_DECREF(jsonModule);
            if (loadsFunc) {
                PyObject *jsonArgs = PyTuple_New(1);
                PyTuple_SetItem(jsonArgs, 0, PyUnicode_FromString(brandConfigJson));
                PyObject *configDict = PyObject_CallObject(loadsFunc, jsonArgs);
                Py_DECREF(loadsFunc);
                Py_DECREF(jsonArgs);
                if (configDict) {
                    args = PyTuple_New(1);
                    PyTuple_SetItem(args, 0, configDict);
                }
            }
        }
    }

    if (!args) {
        args = PyTuple_New(0);
    }

    PyObject *instance = PyObject_CallObject(class, args);
    Py_DECREF(args);
    Py_DECREF(class);

    if (!instance) {
        PyErr_Print();
        return;
    }

    s_novinBridgeInstance = instance;
}

bool novin_python_initialize(const char *pythonHome, const char *pythonPath) {
    if (s_pythonInitialized) {
        return true;
    }

    // Configure Python using PyConfig so codec/encodings are available immediately
    PyStatus status;
    PyConfig config;
    PyConfig_InitIsolatedConfig(&config);

    // Do not read environment; be fully self-contained in framework bundle
    config.isolated = 1;
    config.use_environment = 0;

    // Set Python home if provided (path to Resources/python)
    if (pythonHome && strlen(pythonHome) > 0) {
        s_pythonHomeW = Py_DecodeLocale(pythonHome, NULL);
        if (!s_pythonHomeW) {
            PyConfig_Clear(&config);
            return false;
        }
        status = PyConfig_SetString(&config, &config.home, s_pythonHomeW);
        if (PyStatus_Exception(status)) {
            PyConfig_Clear(&config);
            return false;
        }
    }

    // Add module search paths if provided (colon-separated)
    if (pythonPath && strlen(pythonPath) > 0) {
        // Duplicate string as we'll mutate while splitting
        char *mutablePath = strdup(pythonPath);
        if (!mutablePath) {
            PyConfig_Clear(&config);
            return false;
        }
        char *saveptr = NULL;
        const char *delim = ":";
        for (char *token = strtok_r(mutablePath, delim, &saveptr);
             token != NULL;
             token = strtok_r(NULL, delim, &saveptr)) {
            wchar_t *wpath = Py_DecodeLocale(token, NULL);
            if (!wpath) { continue; }
            status = PyWideStringList_Append(&config.module_search_paths, wpath);
            PyMem_RawFree(wpath);
            if (PyStatus_Exception(status)) {
                free(mutablePath);
                PyConfig_Clear(&config);
                return false;
            }
        }
        free(mutablePath);
    }

    status = Py_InitializeFromConfig(&config);
    if (PyStatus_Exception(status) || !Py_IsInitialized()) {
        PyConfig_Clear(&config);
        PyErr_Print();
        return false;
    }
    PyConfig_Clear(&config);

    // Prepare GIL for multi-threaded use; release it for the embedding app
    s_mainThreadState = PyEval_SaveThread();
    s_pythonInitialized = true;
    return true;
}

const char *novin_python_process_request(const char *requestJson,
                                         const char *clientId,
                                         const char *brandConfigJson,
                                         const char **errorOut) {
    if (!s_pythonInitialized) {
        if (errorOut) {
            *errorOut = strdup("Python runtime not initialized");
        }
        return NULL;
    }

    PyGILState_STATE gilState = PyGILState_Ensure();

    if (!s_novinBridgeInstance) {
        ensure_bridge_initialized(brandConfigJson);
        if (!s_novinBridgeInstance) {
            PyGILState_Release(gilState);
            if (errorOut) {
                *errorOut = strdup("Failed to initialize NovinAIBridge");
            }
            return NULL;
        }
    }

    PyObject *processFunc = PyObject_GetAttrString(s_novinBridgeInstance, "process_request");
    if (!processFunc) {
        PyErr_Print();
        PyGILState_Release(gilState);
        if (errorOut) {
            *errorOut = strdup("NovinAIBridge missing process_request");
        }
        return NULL;
    }

    PyObject *args = PyTuple_New(2);
    PyTuple_SetItem(args, 0, PyUnicode_FromString(requestJson));
    const char *actualClientId = clientId ? clientId : "ios-client";
    PyTuple_SetItem(args, 1, PyUnicode_FromString(actualClientId));

    PyObject *result = PyObject_CallObject(processFunc, args);
    Py_DECREF(args);
    Py_DECREF(processFunc);

    if (!result) {
        PyErr_Print();
        PyGILState_Release(gilState);
        if (errorOut) {
            *errorOut = strdup("Python processing failed");
        }
        return NULL;
    }

    const char *resultCString = PyUnicode_AsUTF8(result);
    if (!resultCString) {
        Py_DECREF(result);
        PyGILState_Release(gilState);
        if (errorOut) {
            *errorOut = strdup("Failed to convert Python result to UTF-8");
        }
        return NULL;
    }

    char *response = strdup(resultCString);
    Py_DECREF(result);
    PyGILState_Release(gilState);
    if (!response && errorOut) {
        *errorOut = strdup("Out of memory duplicating response");
    }
    return response;
}

void novin_python_free_string(const char *string) {
    if (string) {
        free((void *)string);
    }
}

void novin_python_finalize(void) {
    if (!s_pythonInitialized) {
        return;
    }

    if (s_mainThreadState) {
        PyEval_RestoreThread(s_mainThreadState);
        s_mainThreadState = NULL;
    }

    PyGILState_STATE gilState = PyGILState_Ensure();
    Py_XDECREF(s_novinBridgeInstance);
    s_novinBridgeInstance = NULL;
    PyGILState_Release(gilState);

    Py_Finalize();
    s_pythonInitialized = false;

    if (s_pythonHomeW) {
        PyMem_RawFree(s_pythonHomeW);
        s_pythonHomeW = NULL;
    }
    if (s_pythonPathW) {
        PyMem_RawFree(s_pythonPathW);
        s_pythonPathW = NULL;
    }
}


