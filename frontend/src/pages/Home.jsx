import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileText, Clock, ChevronRight, Mic, Trash2 } from 'lucide-react';
import { uploadPDF, getLibrary, deleteDocument } from '../utils/api';
import ActionToast from '../components/ActionToast';
import './Home.css';

const Home = () => {
    const navigate = useNavigate();
    const [recentDocs, setRecentDocs] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        const loadRecent = async () => {
            try {
                const data = await getLibrary();
                if (data && data.documents) {
                    setRecentDocs(data.documents);
                }
            } catch (e) {
                console.error("Failed to load recent sessions", e);
            }
        };
        loadRecent();
    }, []);

    const handleFileChange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setLoading(true);
        try {
            const data = await uploadPDF(file);
            navigate('/tutor', { state: { ...data, docId: data.pdf_id, autoStart: true } });
        } catch (err) {
            setError(err.message || "Upload failed");
            setLoading(false);
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm("Are you sure you want to delete this session?")) return;
        try {
            await deleteDocument(id);
            setRecentDocs(prev => prev.filter(doc => doc.id !== id));
        } catch (e) {
            setError("Failed to delete document");
        }
    };

    return (
        <div className="home-layout">
            <header className="home-header">
                <div className="logo-section">
                    <div className="logo-icon"><Mic size={24} color="white" /></div>
                    <h2>VoiceTutor</h2>
                </div>
            </header>

            <main className="dashboard">
                <section className="hero-section">
                    <h1>Welcome Back, <br />Let's Learn Something New</h1>
                    <p className="text-muted">Upload a PDF or continue where you left off. Your AI assistant is ready.</p>
                </section>

                <div className="action-grid">
                    {/* Primary Action: Upload */}
                    <div className="card upload-card hover-lift">
                        <input
                            id="pdf-upload"
                            type="file"
                            accept=".pdf"
                            onChange={handleFileChange}
                            className="hidden"
                            disabled={loading}
                        />
                        <label htmlFor="pdf-upload" className="upload-label">
                            <div className="icon-circle primary">
                                <Upload size={32} />
                            </div>
                            <h3>Upload New Document</h3>
                            <p className="text-muted">PDF files supported</p>
                            {loading && <div className="loading-badge">Uploading...</div>}
                        </label>
                    </div>

                    {/* Secondary: Recent */}
                    <div className="card recent-card hover-lift">
                        <div className="card-header">
                            <h3><Clock size={20} /> Recent Sessions</h3>
                        </div>
                        <ul className="recent-list">
                            {recentDocs.length === 0 ? (
                                <li className="recent-item" style={{ justifyContent: 'center', color: '#888' }}>No recent files found.</li>
                            ) : (
                                recentDocs.map((doc) => (
                                    <li key={doc.id} className="recent-item" onClick={() => navigate('/tutor', { state: { docId: doc.id, filename: doc.filename, page_count: '?', autoStart: true } })}>
                                        <div className="file-icon"><FileText size={20} /></div>
                                        <div className="file-info">
                                            <span className="file-name">{doc.filename}</span>
                                            <span className="file-date">PDF Document</span>
                                        </div>
                                        <button
                                            className="btn-icon delete-btn"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleDelete(doc.id);
                                            }}
                                            title="Delete"
                                        >
                                            <Trash2 size={18} />
                                        </button>
                                        <ChevronRight className="arrow" size={16} />
                                    </li>
                                ))
                            )}
                        </ul>
                    </div>
                </div>
            </main>
            {error && <ActionToast message={error} type="error" onClose={() => setError(null)} />}
        </div>
    );
};

export default Home;
