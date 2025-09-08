# A2Dev Gap Implementation Proposals

## Philosophy
These implementations maintain A2Dev's core principle: **provide structure, not prescription**. Each feature offers containers and hooks that LLMs can use or ignore.

---

## Gap 1: Base-Layer Collaboration Features

### Current State
- Collaboration exists only in optional intelligence layer
- No built-in mechanisms for multi-stakeholder input

### Proposed Implementation: Collaboration Hooks

```python
# a2a/core/collaboration.py
from pathlib import Path
import json
from typing import Dict, List, Optional
from datetime import datetime

class CollaborationHooks:
    """Lightweight collaboration without prescription"""
    
    def __init__(self):
        self.feedback_dir = Path('.a2dev/feedback')
        self.feedback_dir.mkdir(parents=True, exist_ok=True)
    
    def capture_feedback(self, artifact_type: str, content: str, 
                        stakeholder: str = "stakeholder") -> str:
        """Create a feedback file that LLMs can check if they want"""
        timestamp = datetime.now().isoformat()
        feedback_file = self.feedback_dir / f"{artifact_type}_{timestamp}.json"
        
        feedback_file.write_text(json.dumps({
            'artifact_type': artifact_type,
            'stakeholder': stakeholder,
            'feedback': content,
            'timestamp': timestamp,
            'status': 'pending'  # LLM can mark as 'addressed' or 'declined'
        }, indent=2))
        
        return str(feedback_file)
    
    def list_feedback(self, artifact_type: Optional[str] = None, 
                     status: str = 'pending') -> List[Dict]:
        """List feedback files - LLM decides whether to read them"""
        feedback = []
        for f in self.feedback_dir.glob('*.json'):
            data = json.loads(f.read_text())
            if (not artifact_type or data['artifact_type'] == artifact_type) and \
               data['status'] == status:
                feedback.append(data)
        return feedback
    
    def comment_anchor(self, file_path: str, line_num: int) -> str:
        """Return a comment anchor format that LLMs can recognize"""
        # Simple convention that LLMs can learn
        return f"# FEEDBACK_REQUESTED: {file_path}:{line_num}"
```

### CLI Integration
```python
# Add to a2dev_cli.py
@cli.command()
@click.argument('artifact_type')
@click.option('--from', 'stakeholder', default='user')
def feedback(artifact_type: str, stakeholder: str):
    """Capture stakeholder feedback (LLM will see it on next run)"""
    print(f"Enter feedback for {artifact_type} (Ctrl+D to finish):")
    import sys
    content = sys.stdin.read()
    
    hooks = CollaborationHooks()
    file_path = hooks.capture_feedback(artifact_type, content, stakeholder)
    print(f"Feedback saved to {file_path}")
    print("The LLM will see this on the next artifact generation.")

@cli.command()
def show_feedback():
    """Show pending feedback"""
    hooks = CollaborationHooks()
    feedback = hooks.list_feedback()
    for item in feedback:
        print(f"\n[{item['stakeholder']}] {item['artifact_type']}:")
        print(item['feedback'])
```

### Role Integration (Optional)
```python
# a2a/roles/base.py - Base class other roles can inherit
class CollaborativeRole:
    """Mixin for roles that want to check feedback"""
    
    def check_feedback(self, artifact_type: str) -> List[str]:
        """Roles can optionally call this"""
        hooks = CollaborationHooks()
        feedback = hooks.list_feedback(artifact_type)
        return [f['feedback'] for f in feedback]
    
    def get_feedback_context(self) -> str:
        """Return feedback as context string - LLM decides how to use it"""
        feedback = self.check_feedback(self.__class__.__name__)
        if feedback:
            return "\n## Stakeholder Feedback\n" + "\n".join(f"- {f}" for f in feedback)
        return ""
```

**Key Design Points:**
- No forced workflow - LLMs choose whether to check feedback
- Simple file-based storage - easy to understand and modify
- Convention over configuration - comment anchors LLMs can learn
- Stakeholder attribution without role prescription

---

## Gap 2: Retrospective Support

### Current State
- No reflection mechanisms
- No capture of lessons learned

### Proposed Implementation: Retrospective Templates

```python
# a2a/core/retrospective.py
from pathlib import Path
from typing import Dict, Optional
import json

class RetrospectiveTemplates:
    """Provide structure for retrospectives without forcing them"""
    
    def __init__(self):
        self.retro_dir = Path('.a2dev/retrospectives')
        self.retro_dir.mkdir(parents=True, exist_ok=True)
    
    def start_retro(self, sprint_id: Optional[str] = None) -> str:
        """Create empty retro structure - LLM fills it or ignores it"""
        sprint = sprint_id or datetime.now().strftime('%Y-%W')
        
        template = {
            'sprint': sprint,
            'timestamp': datetime.now().isoformat(),
            'sections': {
                'went_well': [],      # LLM can add items
                'needs_improvement': [],
                'action_items': [],
                'metrics': {},        # LLM can add any metrics
                'notes': ""          # Free-form section
            }
        }
        
        retro_file = self.retro_dir / f"sprint_{sprint}.json"
        retro_file.write_text(json.dumps(template, indent=2))
        return str(retro_file)
    
    def get_retro_markdown(self) -> str:
        """Return markdown template - LLM can modify or ignore"""
        return """# Sprint Retrospective

## What Went Well
- 

## What Needs Improvement
- 

## Action Items
- [ ] 

## Metrics & Observations
- 

## Team Notes
"""
    
    def suggest_questions(self) -> List[str]:
        """Optional prompts - LLM decides if/how to use them"""
        return [
            "What was our velocity this sprint?",
            "Which artifacts took longest to generate?",
            "What feedback patterns emerged?",
            "Were estimates accurate?",
            "What would we do differently?"
        ]
```

### Orchestrator Integration
```python
# Add to a2a/orchestrator.py
def complete_sprint(self, sprint_id: Optional[str] = None) -> dict:
    """Optional sprint completion - creates retro template"""
    retro = RetrospectiveTemplates()
    retro_file = retro.start_retro(sprint_id)
    
    # Just create the structure - don't force any workflow
    return {
        'retro_template': retro_file,
        'message': 'Retrospective template created. LLM can fill it during next session.'
    }
```

### Auto-Learning Pattern
```python
# a2a/core/patterns.py
class PatternLearning:
    """Detect patterns across retrospectives - LLM can use these insights"""
    
    def find_patterns(self) -> Dict:
        """Find recurring themes across retros"""
        retro_dir = Path('.a2dev/retrospectives')
        patterns = {
            'common_improvements': {},
            'recurring_actions': {},
            'velocity_trends': []
        }
        
        for retro_file in retro_dir.glob('*.json'):
            data = json.loads(retro_file.read_text())
            # Count occurrences of improvement items
            for item in data['sections'].get('needs_improvement', []):
                patterns['common_improvements'][item] = \
                    patterns['common_improvements'].get(item, 0) + 1
        
        return patterns
```

**Key Design Points:**
- Templates are suggestions, not requirements
- Pattern detection helps LLMs learn from history
- No mandatory fields or workflows
- Sprint-agnostic (works with any cadence)

---

## Gap 3: Metrics Visualization Dashboard

### Current State
- Metrics collected but not visualized
- No easy way to track performance

### Proposed Implementation: Lightweight Metrics Viewer

```python
# a2a/core/metrics.py
import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime, timedelta

class MetricsCollector:
    """Passive metrics collection - no performance impact"""
    
    def __init__(self):
        self.metrics_file = Path('.a2dev/metrics.jsonl')
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
    
    def record(self, event_type: str, data: Dict) -> None:
        """Append-only metrics log"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'event': event_type,
            'data': data
        }
        with self.metrics_file.open('a') as f:
            f.write(json.dumps(entry) + '\n')
    
    def get_summary(self, hours: int = 24) -> Dict:
        """Simple aggregation for recent activity"""
        if not self.metrics_file.exists():
            return {}
        
        cutoff = datetime.now() - timedelta(hours=hours)
        summary = {
            'artifact_counts': {},
            'generation_times': [],
            'cache_hits': 0,
            'cache_misses': 0,
            'error_count': 0
        }
        
        with self.metrics_file.open() as f:
            for line in f:
                entry = json.loads(line)
                timestamp = datetime.fromisoformat(entry['timestamp'])
                if timestamp > cutoff:
                    self._aggregate_entry(entry, summary)
        
        return summary
    
    def _aggregate_entry(self, entry: Dict, summary: Dict) -> None:
        """Add entry to summary stats"""
        event = entry['event']
        data = entry['data']
        
        if event == 'artifact_generated':
            artifact_type = data.get('type', 'unknown')
            summary['artifact_counts'][artifact_type] = \
                summary['artifact_counts'].get(artifact_type, 0) + 1
            if 'duration' in data:
                summary['generation_times'].append(data['duration'])
        
        elif event == 'cache_hit':
            summary['cache_hits'] += 1
        elif event == 'cache_miss':
            summary['cache_misses'] += 1
        elif event == 'error':
            summary['error_count'] += 1
```

### Terminal Dashboard
```python
# a2a/core/dashboard.py
class TerminalDashboard:
    """Simple terminal-based metrics display"""
    
    def show(self, hours: int = 24) -> str:
        """Generate ASCII dashboard"""
        collector = MetricsCollector()
        summary = collector.get_summary(hours)
        
        if not summary:
            return "No metrics available yet."
        
        # Build simple ASCII visualization
        lines = [
            "═" * 50,
            f"  A2Dev Metrics Dashboard (last {hours}h)",
            "═" * 50,
            ""
        ]
        
        # Artifact generation stats
        if summary['artifact_counts']:
            lines.append("📊 Artifacts Generated:")
            for artifact_type, count in summary['artifact_counts'].items():
                bar = "█" * min(count, 20)
                lines.append(f"  {artifact_type:12} {bar} {count}")
            lines.append("")
        
        # Performance stats
        if summary['generation_times']:
            avg_time = sum(summary['generation_times']) / len(summary['generation_times'])
            lines.append(f"⚡ Performance:")
            lines.append(f"  Avg Generation: {avg_time:.2f}s")
            lines.append(f"  Min: {min(summary['generation_times']):.2f}s")
            lines.append(f"  Max: {max(summary['generation_times']):.2f}s")
            lines.append("")
        
        # Cache stats
        total_cache = summary['cache_hits'] + summary['cache_misses']
        if total_cache > 0:
            hit_rate = (summary['cache_hits'] / total_cache) * 100
            lines.append(f"💾 Cache Performance:")
            lines.append(f"  Hit Rate: {hit_rate:.1f}%")
            lines.append(f"  Hits: {summary['cache_hits']} | Misses: {summary['cache_misses']}")
            lines.append("")
        
        # Error tracking
        if summary['error_count'] > 0:
            lines.append(f"⚠️  Errors: {summary['error_count']}")
            lines.append("")
        
        lines.append("═" * 50)
        
        return "\n".join(lines)
```

### Web Dashboard (Optional Progressive Enhancement)
```python
# a2a/intelligence/web_dashboard.py
class WebDashboard:
    """Optional web-based dashboard - only if intelligence layer enabled"""
    
    def generate_html(self) -> str:
        """Generate static HTML with inline JS for charts"""
        collector = MetricsCollector()
        summary = collector.get_summary(24*7)  # Week view
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>A2Dev Metrics</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: system-ui; padding: 20px; background: #f5f5f5; }}
        .metric-card {{ background: white; padding: 20px; margin: 10px; 
                       border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #2563eb; }}
        .metric-label {{ color: #64748b; margin-top: 5px; }}
    </style>
</head>
<body>
    <h1>A2Dev Performance Metrics</h1>
    
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px;">
        <div class="metric-card">
            <div class="metric-value">{len(summary.get('generation_times', []))}</div>
            <div class="metric-label">Artifacts Generated</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{summary.get('cache_hits', 0) / max(1, summary.get('cache_hits', 0) + summary.get('cache_misses', 0)) * 100:.1f}%</div>
            <div class="metric-label">Cache Hit Rate</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{sum(summary.get('generation_times', [0])) / max(1, len(summary.get('generation_times', [1]))):.2f}s</div>
            <div class="metric-label">Avg Generation Time</div>
        </div>
    </div>
    
    <div id="timeline"></div>
    <div id="artifacts"></div>
    
    <script>
        // Plotly charts for trends
        // Data: {json.dumps(summary)}
    </script>
</body>
</html>"""
```

### CLI Integration
```python
# Add to a2dev_cli.py
@cli.command()
@click.option('--hours', default=24, help='Hours to look back')
@click.option('--web', is_flag=True, help='Generate HTML dashboard')
def metrics(hours: int, web: bool):
    """Show metrics dashboard"""
    if web:
        # Only if intelligence layer is enabled
        if Path('.a2dev/intelligence.yaml').exists():
            from a2a.intelligence.web_dashboard import WebDashboard
            dashboard = WebDashboard()
            html = dashboard.generate_html()
            output_file = Path('.a2dev/dashboard.html')
            output_file.write_text(html)
            print(f"Dashboard saved to {output_file}")
            print(f"Open in browser: file://{output_file.absolute()}")
        else:
            print("Web dashboard requires intelligence layer. Showing terminal version:")
            web = False
    
    if not web:
        from a2a.core.dashboard import TerminalDashboard
        dashboard = TerminalDashboard()
        print(dashboard.show(hours))
```

**Key Design Points:**
- Passive collection - no performance impact
- Append-only log - simple and reliable
- Terminal-first - works everywhere
- Web dashboard only with intelligence layer
- No external dependencies for core metrics

---

## Implementation Strategy

### Phase 1: Core Hooks (1 day)
- Add collaboration hooks
- Add retrospective templates
- No breaking changes

### Phase 2: Metrics Collection (1 day)
- Add passive metrics collector
- Integrate with existing orchestrator
- Terminal dashboard only

### Phase 3: Optional Enhancements (2 days)
- Web dashboard in intelligence layer
- Pattern learning from retrospectives
- Advanced collaboration features

### Integration Points

```python
# Example: Orchestrator automatically records metrics
class Orchestrator:
    def prepare_story(self, story_id: int) -> dict:
        start_time = time.time()
        metrics = MetricsCollector()
        
        try:
            # Existing logic...
            result = self._generate_artifacts(story_id)
            
            # Record success
            metrics.record('artifact_generated', {
                'type': 'story',
                'id': story_id,
                'duration': time.time() - start_time
            })
            
            return result
        except Exception as e:
            # Record error
            metrics.record('error', {
                'type': 'story_generation',
                'id': story_id,
                'error': str(e)
            })
            raise
```

---

## Summary

These implementations maintain A2Dev's core philosophy:

1. **Structure, not prescription**: All features provide containers that LLMs can use or ignore
2. **Zero mandatory workflows**: Everything is optional
3. **Progressive enhancement**: Basic features in core, advanced in intelligence layer
4. **Clean architecture**: Each feature is isolated and removable
5. **Performance first**: No impact on core generation speed

Total estimated LOC addition:
- Core: ~300 lines (keeps under 1000 total)
- Intelligence: ~200 lines (optional)
- Maintains goal of lightweight, understandable codebase