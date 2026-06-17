package com.agentorchestrator.controller;

import com.agentorchestrator.service.AgentService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/admin/tools")
public class ToolController {

    private final AgentService agentService;

    public ToolController(AgentService agentService) {
        this.agentService = agentService;
    }

    @GetMapping
    public ResponseEntity<Map<String, Object>> listTools(@RequestParam(required = false) String category) {
        return ResponseEntity.ok(agentService.listTools(category));
    }
}
