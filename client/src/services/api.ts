import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

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
}

export interface ChildUpdate {
  target_topic?: string;
  age_level?: number;
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

  getChildTopics: async (childId: string) => {
    const response = await apiClient.get(`/parent/children/${childId}/topics`);
    return response.data;
  },

  addChildTopic: async (childId: string, topic: string, setAsActive: boolean = false) => {
    const response = await apiClient.post(`/parent/children/${childId}/topics`, {
      topic,
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
};
