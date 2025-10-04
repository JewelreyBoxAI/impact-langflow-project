// In: frontend/app/lib/api.ts
import axios from "axios";

const axiosInstance = axios.create({
  baseURL: "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

// Define the structure of the data the function will receive
interface SendMessagePayload {
  message: string;
  flow_id: string; // The ID of your Langflow flow
  sessionId?: string;
}

// Update the sendMessage function to accept the single payload object
const sendMessage = async (payload: SendMessagePayload) => {
  try {
    // Create the payload that the backend /api/flows/run endpoint expects
    const apiPayload = {
      flow_id: payload.flow_id,
      parameters: {
        // This "input_value" MUST match the name of the input field
        // in your Langflow Chat Input component
        input_value: payload.message
      },
      session_id: payload.sessionId,
    };

    // Call the correct endpoint
    const response = await axiosInstance.post('/api/flows/run', apiPayload);
    return response.data;
  } catch (error) {
    console.error("Error in apiClient.sendMessage:", error);
    throw error;
  }
};

export const apiClient = {
  sendMessage,
};