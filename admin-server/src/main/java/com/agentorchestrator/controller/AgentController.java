package com.agentorchestrator.controller;

import com.agentorchestrator.model.Agent;
import com.agentorchestrator.service.AgentService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/admin/agents")
public class AgentController {

    private final AgentService agentService;

    public AgentController(AgentService agentService) {
        this.agentService = agentService;
    }

    @PostMapping
    public ResponseEntity<Map<String, Object>> createAgent(@Valid @RequestBody Agent agent) {
        return ResponseEntity.ok(agentService.createAgent(agent));
    }

    @GetMapping
    public ResponseEntity<Map<String, Object>> listAgents() {
        return ResponseEntity.ok(agentService.listAgentsFromCore());
    }

    @PostMapping("/{agentName}/run")
    public ResponseEntity<Map<String, Object>> runAgent(
            @PathVariable String agentName,
            @RequestBody Map<String, String> request) {
        String task = request.getOrDefault("task", "");
        return ResponseEntity.ok(agentService.runAgent(agentName, task));
    }

    @DeleteMapping("/{agentName}")
    public ResponseEntity<Map<String, Object>> deleteAgent(@PathVariable String agentName) {
        return ResponseEntity.ok(agentService.deleteAgent(agentName));
    }
}
