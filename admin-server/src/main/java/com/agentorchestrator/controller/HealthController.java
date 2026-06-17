package com.agentorchestrator.controller;

import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

@RestController
public class HealthController {

    private final RestTemplate restTemplate;

    public HealthController(@Qualifier("agentCoreRestTemplate") RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    @GetMapping("/api/admin/health")
    public ResponseEntity<Map<String, Object>> health() {
        Map<String, Object> coreHealth;
        try {
            coreHealth = restTemplate.getForObject("/health", Map.class);
        } catch (Exception e) {
            coreHealth = Map.of("error", "Agent Core unreachable: " + e.getMessage());
        }

        return ResponseEntity.ok(Map.of(
                "admin_server", "ok",
                "agent_core", coreHealth
        ));
    }
}
