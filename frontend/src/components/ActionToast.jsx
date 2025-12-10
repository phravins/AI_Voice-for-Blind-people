import React, { useEffect } from 'react';
import './ActionToast.css';

const ActionToast = ({ message, type = 'info', onClose }) => {
    useEffect(() => {
        const timer = setTimeout(() => {
            onClose();
        }, 3000);
        return () => clearTimeout(timer);
    }, [onClose]);

    return (
        <div className={`action-toast ${type}`}>
            {message}
        </div>
    );
};

export default ActionToast;
