import React from 'react';
import { BookOpen, HelpCircle, GraduationCap, Languages } from 'lucide-react';

const ContextCard = ({ title, summary, onAction }) => {
    return (
        <div className="card context-card">
            <h3 className="context-title">{title || "Current Context"}</h3>
            <p className="context-summary text-muted">
                {summary || "Content is ready. Ask me to summarize or explain."}
            </p>

            <div className="quick-actions">
                <button className="action-btn" onClick={() => onAction('SUMMARIZE')}>
                    <BookOpen size={18} /> Summarize
                </button>
                <button className="action-btn" onClick={() => onAction('EXPLAIN')}>
                    <HelpCircle size={18} /> Explain
                </button>
                <button className="action-btn" onClick={() => onAction('QUIZ')}>
                    <GraduationCap size={18} /> Quiz
                </button>
                <button className="action-btn" onClick={() => onAction('TRANSLATE')}>
                    <Languages size={18} /> Translate
                </button>
            </div>
        </div>
    );
};

// Simple inline styles for specific component layout or could be in CSS
// I will assume global CSS covers .card, but .quick-actions needs layout
// I'll add a <style> block or just update index.css later. 
// For now, let's keep it simple with a style tag here for speed or import CSS.
// I'll make ContextCard.css
export default ContextCard;
