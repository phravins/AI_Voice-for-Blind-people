import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import Tutor from './pages/Tutor';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/tutor" element={<Tutor />} />
      </Routes>
    </Router>
  );
}

export default App;
