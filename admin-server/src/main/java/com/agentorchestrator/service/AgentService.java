package com.agentorchestrator.service;

import com.agentorchestrator.model.Agent;
import com.agentorchestrator.model.AgentStatus;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.List;
import java.util.Map;

@Service
public class AgentService {

    private final RestTemplate restTemplate;
    private final String agentCoreBaseUrl;

    public AgentService(@Qualifier("agentCoreRestTemplate") RestTemplate restTemplate,
                        @Qualifier("agentCoreBaseUrl") String agentCoreBaseUrl) {
        this.restTemplate = restTemplate;
        this.agentCoreBaseUrl = agentCoreBaseUrl;
    }

    /**
     * 向 Python Agent Core 注册新 Agent
     */
    public Map<String, Object> createAgent(Agent agent) {
        Map<String, Object> request = Map.of(
                "name", agent.getName(),
                "description", agent.getDescription() != null ? agent.getDescription() : "",
                "system_prompt", agent.getSystemPrompt() != null ? agent.getSystemPrompt() : "You are a helpful assistant.",
                "tools", agent.getTools() != null ? agent.getTools() : List.of(),
                "max_iterations", agent.getMaxIterations() != null ? agent.getMaxIterations() : 10,
                "temperature", agent.getTemperature() != null ? agent.getTemperature() : 0.7
        );

        ResponseEntity<Map<String, Object>> response = restTemplate.exchange(
                "/api/agents",
                HttpMethod.POST,
                new org.springframework.http.HttpEntity<>(request),
                new ParameterizedTypeReference<>() {}
        );
        return response.getBody();
    }

    /**
     * 获取所有 Agent 列表 (从 Python Core 查询实时状态)
     */
    public Map<String, Object> listAgentsFromCore() {
        ResponseEntity<Map<String, Object>> response = restTemplate.exchange(
                "/api/agents",
                HttpMethod.GET,
                null,
                new ParameterizedTypeReference<>() {}
        );
        return response.getBody();
    }

    /**
     * 执行 Agent 任务
     */
    public Map<String, Object> runAgent(String agentName, String task) {
        Map<String, String> request = Map.of(
                "agent_name", agentName,
                "task", task
        );

        ResponseEntity<Map<String, Object>> response = restTemplate.exchange(
                "/api/agents/" + agentName + "/run",
                HttpMethod.POST,
                new org.springframework.http.HttpEntity<>(request),
                new ParameterizedTypeReference<>() {}
        );
        return response.getBody();
    }

    /**
     * 删除 Agent
     */
    public Map<String, Object> deleteAgent(String agentName) {
        ResponseEntity<Map<String, Object>> response = restTemplate.exchange(
                "/api/agents/" + agentName,
                HttpMethod.DELETE,
                null,
                new ParameterizedTypeReference<>() {}
        );
        return response.getBody();
    }

    /**
     * 获取可用工具列表
     */
    public Map<String, Object> listTools(String category) {
        String url = "/api/tools";
        if (category != null && !category.isEmpty()) {
            url += "?category=" + category;
        }
        ResponseEntity<Map<String, Object>> response = restTemplate.exchange(
                url,
                HttpMethod.GET,
                null,
                new ParameterizedTypeReference<>() {}
        );
        return response.getBody();
    }
}
