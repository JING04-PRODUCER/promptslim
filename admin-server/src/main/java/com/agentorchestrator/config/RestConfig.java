package com.agentorchestrator.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestTemplate;

import java.time.Duration;

@Configuration
public class RestConfig {

    @Value("${agent-core.base-url}")
    private String agentCoreBaseUrl;

    @Value("${agent-core.connect-timeout}")
    private Duration connectTimeout;

    @Value("${agent-core.read-timeout}")
    private Duration readTimeout;

    @Bean
    public RestTemplate agentCoreRestTemplate(RestTemplateBuilder builder) {
        return builder
                .rootUri(agentCoreBaseUrl)
                .connectTimeout(connectTimeout)
                .readTimeout(readTimeout)
                .build();
    }

    @Bean
    public String agentCoreBaseUrl() {
        return agentCoreBaseUrl;
    }
}
