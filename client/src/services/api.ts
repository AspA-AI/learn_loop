import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('parent_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle 401 errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('parent_token');
      // Don't redirect automatically - let components handle it
    }
    return Promise.reject(error);
  }
);

// Auth API
export interface ParentRegister {
  email: string;
  password: string;
  name?: string;
}

export interface ParentLogin {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  parent_id: string;
  email: string;
  preferred_language?: string;
}

export interface ParentProfile {
  id: string;
  email: string;
  name?: string;
  preferred_language?: string;
}

export const authApi = {
  register: async (data: ParentRegister): Promise<TokenResponse> => {
    const response = await apiClient.post('/auth/register', data);
    const tokenData = response.data;
    localStorage.setItem('parent_token', tokenData.access_token);
    return tokenData;
  },

  login: async (data: ParentLogin): Promise<TokenResponse> => {
    // OAuth2PasswordRequestForm expects form data with username/password
    const formData = new URLSearchParams();
    formData.append('username', data.email);
    formData.append('password', data.password);
    
    const response = await apiClient.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    const tokenData = response.data;
    localStorage.setItem('parent_token', tokenData.access_token);
    return tokenData;
  },

  logout: () => {
    localStorage.removeItem('parent_token');
  },

  isAuthenticated: (): boolean => {
    return !!localStorage.getItem('parent_token');
  },

  getToken: (): string | null => {
    return localStorage.getItem('parent_token');
  },

  getProfile: async (): Promise<ParentProfile> => {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },
};

export interface StartSessionParams {
  learning_code: string;
}

export interface InteractParams {
  sessionId: string;
  message?: string;
  audio?: File;
}

export interface ChildCreate {
  name: string;
  age_level: number;
  learning_style?: string;
  interests?: string[];
  reading_level?: string;
  attention_span?: string;
  strengths?: string[];
  learning_language?: string;
}

export interface ChildUpdate {
  name?: string;
  target_topic?: string;
  age_level?: number;
  learning_style?: string;
  interests?: string[];
  reading_level?: string;
  attention_span?: string;
  strengths?: string[];
  learning_language?: string;
}

export const learningApi = {
  startSession: async (params: StartSessionParams) => {
    const response = await apiClient.post('/sessions/start', params);
    return response.data;
  },

  interact: async ({ sessionId, message, audio }: InteractParams) => {
    const formData = new FormData();
    if (audio) formData.append('audio', audio);
    if (message) formData.append('message', message);
    
    const response = await apiClient.post(`/sessions/${sessionId}/interact`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  endSession: async (sessionId: string) => {
    const response = await apiClient.post(`/sessions/${sessionId}/end`);
    return response.data;
  },

  // --- Parent Endpoints ---

  getChildren: async () => {
    const response = await apiClient.get('/parent/children');
    return response.data;
  },

  createChild: async (data: ChildCreate) => {
    const response = await apiClient.post('/parent/children', data);
    return response.data;
  },

  updateChild: async (childId: string, data: ChildUpdate) => {
    const response = await apiClient.patch(`/parent/children/${childId}`, data);
    return response.data;
  },

  updateParentProfile: async (data: { name?: string; preferred_language?: string }) => {
    const response = await apiClient.patch('/parent/profile', data);
    return response.data;
  },

  uploadCurriculum: async (file: File, childIds: string[]) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('child_ids', JSON.stringify(childIds));
    const response = await apiClient.post('/parent/curriculum/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  getCurriculum: async () => {
    const response = await apiClient.get('/parent/curriculum');
    return response.data;
  },

  removeCurriculum: async (documentId: string) => {
    const response = await apiClient.delete(`/parent/curriculum/${documentId}`);
    return response.data;
  },

  getParentInsights: async (week: string) => {
    const response = await apiClient.get('/parent/insights', {
      params: { week },
    });
    return response.data;
  },

  getChildEvaluations: async (childId: string) => {
    const response = await apiClient.get(`/parent/children/${childId}/evaluations`);
    return response.data;
  },

  getChildSessions: async (childId: string) => {
    const response = await apiClient.get(`/parent/children/${childId}/sessions`);
    return response.data;
  },

  getSessionChat: async (sessionId: string) => {
    const response = await apiClient.get(`/parent/sessions/${sessionId}/chat`);
    return response.data;
  },

  // --- Topic Management ---

  getChildSubjects: async (childId: string) => {
    const response = await apiClient.get(`/parent/children/${childId}/subjects`);
    return response.data.subjects || [];
  },

  getChildTopics: async (childId: string) => {
    const response = await apiClient.get(`/parent/children/${childId}/topics`);
    return response.data;
  },

  addChildTopic: async (childId: string, topic: string, subject: string = "General", setAsActive: boolean = false) => {
    const response = await apiClient.post(`/parent/children/${childId}/topics`, {
      topic,
      subject,
      set_as_active: setAsActive
    });
    return response.data;
  },

  activateTopic: async (childId: string, topicId: string) => {
    const response = await apiClient.patch(`/parent/children/${childId}/topics/${topicId}/activate`);
    return response.data;
  },

  removeChildTopic: async (childId: string, topicId: string) => {
    const response = await apiClient.delete(`/parent/children/${childId}/topics/${topicId}`);
    return response.data;
  },

  // --- Subject Document Management ---

  getSubjectDocuments: async (childId: string, subject: string) => {
    const response = await apiClient.get(`/parent/children/${childId}/subjects/${encodeURIComponent(subject)}/documents`);
    return response.data;
  },

  uploadSubjectDocument: async (childId: string, subject: string, topic: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('topic', topic);
    const response = await apiClient.post(
      `/parent/children/${childId}/subjects/${encodeURIComponent(subject)}/documents`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    );
    return response.data;
  },

  removeSubjectDocument: async (childId: string, subject: string, documentId: string) => {
    const response = await apiClient.delete(`/parent/children/${childId}/subjects/${encodeURIComponent(subject)}/documents/${documentId}`);
    return response.data;
  },

  // --- Quiz Endpoints ---

  startQuiz: async (sessionId: string, numQuestions: number = 5) => {
    const response = await apiClient.post(`/sessions/${sessionId}/quiz/start`, null, {
      params: { num_questions: numQuestions },
    });
    return response.data;
  },

  submitQuizAnswer: async (sessionId: string, answer: string) => {
    const formData = new FormData();
    formData.append('answer', answer);
    const response = await apiClient.post(`/sessions/${sessionId}/quiz/answer`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  cancelQuiz: async (sessionId: string) => {
    const response = await apiClient.post(`/sessions/${sessionId}/quiz/cancel`);
    return response.data;
  },

  // --- Formal Reporting ---

  generateReport: async (childId: string, reportType: 'weekly' | 'monthly' = 'monthly') => {
    const response = await apiClient.get(`/parent/children/${childId}/reports/generate`, {
      params: { report_type: reportType }
    });
    return response.data;
  },

  getReports: async (childId: string) => {
    const response = await apiClient.get(`/parent/children/${childId}/reports`);
    return response.data;
  },

  getReportDetail: async (reportId: string) => {
    const response = await apiClient.get(`/parent/reports/${reportId}`);
    return response.data;
  },

  translateReport: async (reportId: string, targetLanguage: string) => {
    const response = await apiClient.get(`/parent/reports/${reportId}/translate`, {
      params: { target_language: targetLanguage }
    });
    return response.data;
  },
};
