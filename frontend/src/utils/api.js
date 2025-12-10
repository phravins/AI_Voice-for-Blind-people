const API_BASE = ""; // Use relative path for proxy


export async function uploadPDF(file) {
    const formData = new FormData();
    formData.append("pdf", file);

    const response = await fetch(`${API_BASE}/api/upload`, {
        method: "POST",
        body: formData,
    });

    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error || "Upload failed");
    }

    return response.json();
}

export async function sendAction(docId, page, intent, userUtterance, entities = {}) {
    const response = await fetch(`${API_BASE}/api/assistant/action`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            doc_id: docId,
            page,
            intent,
            user_utterance: userUtterance,
            ...entities
        }),
    });

    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error || "Action failed");
    }

    return response.json();
}

export function getAudioUrl(filename) {
    if (!filename) return null;
    if (filename.startsWith("/")) return `${API_BASE}${filename}`;
    return `${API_BASE}/audio/${filename}`;
}

export async function getTTS(text) {
    const params = new URLSearchParams({ text });
    const response = await fetch(`${API_BASE}/api/tts?${params}`);
    if (!response.ok) throw new Error("TTS failed");
    return response.json();
}

export async function getPageContent(docId, pageNum) {
    const response = await fetch(`${API_BASE}/api/doc/${docId}/page/${pageNum}`);
    if (!response.ok) throw new Error("Failed to load page");
    return response.json();
}

export async function getLibrary() {
    const response = await fetch(`${API_BASE}/api/library`);
    if (!response.ok) {
        const text = await response.text();
        console.error("Library fetch failed:", text);
        throw new Error("Failed to load library: " + text);
    }
    return response.json();
}

export async function deleteDocument(docId) {
    const response = await fetch(`${API_BASE}/api/library/${docId}`, {
        method: "DELETE",
    });

    if (!response.ok) {
        throw new Error("Failed to delete document");
    }
    return response.json();
}
