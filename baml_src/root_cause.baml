// Defining a data model.
class RootCauseAnalysis {
  reasoning string @description("A step-by-step analysis of the patterns, common themes, and how the new incident relates.")
  root_cause_summary string @description("A concise summary of the most likely root causes.")
  troubleshooting_steps string[] @description("A numbered list of recommended troubleshooting steps in order of priority.")
}

// Create a function to extract the RootCauseAnalysis from a string.
function AnalyzeIncident(query: string, similar_incidents_str: string) -> RootCauseAnalysis {
  // Specify a client as provider/model-name
  // you can use custom LLM params with a custom client name from clients.baml like "client CustomHaiku"
  client Gemini // Set OPENAI_API_KEY to use this client.
  //{{ ctx.output_format }} is replaced with a JSON schema of the function's return type(RootCauseAnalysis)
  prompt #"
  <task>
   You are an expert SRE assistant. Given a new incident and a list of similar past incidents, analyze the
  patterns to identify common root causes and suggest the next best troubleshooting steps.
  </task>
   
  <new_incident>
   {{ query }}
  </new_incident>
   
  <similar_incidents>
   {{ similar_incidents_str }}
  </similar_incidents>
   
  Produce your final analysis in this exact format:
   {{ ctx.output_format }}
  "#
}



// Test the function with a sample RootCauseAnalysis. Open the VSCode playground to run this.
test jenkins_git_failure {
  functions [AnalyzeIncident]
  args {
    query "Jenkins pipeline failed with Git authentication error: 'remote: HTTP Basic: Access denied. The provided password or token is incorrect or your account has 2FA enabled and you must use a personal access token instead of a password.'"
    similar_incidents_str #"
    <incident>
    Jenkins build failed - Git clone failed with authentication error. Pipeline was working yesterday but started failing today. Error: remote: HTTP Basic: Access denied
    </incident>
    
    <incident>
    CI/CD pipeline failing on Git checkout. Getting 403 Forbidden error when trying to access repository. Personal access token might be expired.
    </incident>
    
    <incident>
    Jenkins unable to pull from GitLab repository. Authentication failing with message about incorrect credentials. Token was regenerated last week.
    </incident>
    "#
  }
}
