import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider } from './context/AuthContext';
import { AppLayout } from './layouts/AppLayout';

import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { TimetablePage } from './pages/TimetablePage';
import { FindRoomPage } from './pages/FindRoomPage';
import { ExamsPage } from './pages/ExamsPage';
import { BookingsPage } from './pages/BookingsPage';
import { SpectraPage } from './pages/SpectraPage';
import { ReschedulingPage } from './pages/ReschedulingPage';
import { AssistantPage } from './pages/AssistantPage';
import { ManualSchedulingPage } from './pages/ManualSchedulingPage';
import { DataImportPage } from './pages/DataImportPage';
import { SettingsPage } from './pages/SettingsPage';
import { SubjectsPage } from './pages/SubjectsPage';

import { FacultyPortalPage } from './pages/FacultyPortalPage';

export const App: React.FC = () => {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />

            <Route element={<AppLayout />}>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/subjects" element={<SubjectsPage />} />
              <Route path="/faculty" element={<FacultyPortalPage />} />
              <Route path="/timetable" element={<TimetablePage />} />
              <Route path="/find-room" element={<FindRoomPage />} />
              <Route path="/exams" element={<ExamsPage />} />
              <Route path="/bookings" element={<BookingsPage />} />
              <Route path="/spectra" element={<SpectraPage />} />
              <Route path="/reschedule" element={<ReschedulingPage />} />
              <Route path="/assistant" element={<AssistantPage />} />
              <Route path="/manual" element={<ManualSchedulingPage />} />
              <Route path="/import" element={<DataImportPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;
