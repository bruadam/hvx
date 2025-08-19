"""
AI-Powered Graph Analysis for IEQ Analytics Reports
"""

import os
import json
import base64
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from mistralai import Mistral
    from mistralai.models import TextChunk
    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False
    Mistral = None
    TextChunk = None

logger = logging.getLogger(__name__)


@dataclass
class GraphAnalysis:
    """Container for AI-generated graph analysis."""
    chart_name: str
    chart_type: str
    ai_commentary: str
    confidence_score: float
    key_insights: List[str]
    suggested_actions: List[str]
    data_context: Dict[str, Any]
    reviewed: bool = False
    final_commentary: Optional[str] = None


class AIGraphAnalyzer:
    """AI-powered graph analysis using Mistral Vision API for IEQ charts."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "pixtral-large-2411"):
        """Initialize AI Graph Analyzer."""
        if not MISTRAL_AVAILABLE:
            logger.warning("Mistral AI package not available.")
            self.client = None
            self.api_key = None
            self.model = model
            return
            
        self.api_key = api_key or os.getenv('MISTRAL_API_KEY')
        if not self.api_key:
            logger.warning("No Mistral API key provided.")
            self.client = None
            self.model = model
            return
            
        self.model = model
        if Mistral is not None:
            self.client = Mistral(api_key=self.api_key)
        else:
            self.client = None
            
        # Comprehensive system prompt for IEQ analysis
        self.system_prompt = """You are an expert Indoor Environmental Quality (IEQ) analyst specializing in building performance and occupant comfort. You analyze charts and graphs related to temperature, humidity, CO2 levels, air quality, and other environmental parameters in buildings.

Your role is to:
1. Analyze the chart data and identify trends, patterns, and anomalies
2. Assess compliance with standards like EN 16798-1:2019 Category II for office environments
3. Provide actionable insights for building operators and facility managers
4. Suggest specific improvements or interventions when needed

For temperature charts:
- Ideal range: 20-24°C (heating season), 22-26°C (cooling season)
- Look for stability, extreme values, and control effectiveness

For humidity charts:
- Ideal range: 25-60% relative humidity
- Watch for condensation risk (>60%) or dry conditions (<25%)

For CO2 charts:
- Target: <800 ppm above outdoor levels (typically <1200 ppm total)
- Indicates ventilation effectiveness and occupancy patterns

Provide your analysis in JSON format with these fields:
{
    "summary": "Brief 2-3 sentence overview of what the chart shows",
    "key_findings": ["List of 3-5 key observations about the data"],
    "recommendations": ["List of 2-4 specific actionable recommendations"],
    "compliance_assessment": "Assessment of compliance with relevant standards",
    "confidence": 0.85
}

Be specific, practical, and focus on actionable insights that building operators can use to improve indoor environmental quality."""

    def analyze_chart(self, chart_path: Path, chart_context: Dict[str, Any], 
                     chart_type: str = "time_series") -> GraphAnalysis:
        """Analyze a chart image using Mistral Vision API."""
        if not self.client:
            logger.warning("Mistral client not available. Creating fallback analysis.")
            return self._create_fallback_analysis(chart_path, chart_context, chart_type)
            
        try:
            # Read and encode image
            if not chart_path.exists():
                raise FileNotFoundError(f"Chart file not found: {chart_path}")
                
            image_b64 = self._encode_image(chart_path)
            
            # Create context-aware prompt
            context_prompt = self._create_context_prompt(chart_context)
            
            # Call Mistral API using official client
            response = self._call_mistral_client(image_b64, context_prompt)
            
            # Parse response
            analysis_data = self._parse_response(response)
            
            return GraphAnalysis(
                chart_name=chart_path.stem,
                chart_type=chart_type,
                ai_commentary=analysis_data.get('summary', 'No analysis available'),
                confidence_score=analysis_data.get('confidence', 0.0),
                key_insights=analysis_data.get('key_findings', []),
                suggested_actions=analysis_data.get('recommendations', []),
                data_context=chart_context
            )
            
        except Exception as e:
            logger.error(f"AI analysis failed for {chart_path}: {e}")
            return self._create_fallback_analysis(chart_path, chart_context, chart_type)
    
    def _encode_image(self, image_path: Path) -> str:
        """Convert image to base64 string."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def _create_context_prompt(self, context: Dict[str, Any]) -> str:
        """Create a context-aware prompt based on chart metadata."""
        prompt_parts = []
        
        if 'room_id' in context:
            prompt_parts.append(f"Room: {context['room_id']}")
        if 'building_id' in context:
            prompt_parts.append(f"Building: {context['building_id']}")
        if 'parameter' in context:
            prompt_parts.append(f"Parameter: {context['parameter']}")
        if 'description' in context:
            prompt_parts.append(f"Description: {context['description']}")
            
        context_info = " | ".join(prompt_parts)
        
        return f"""Analyze this IEQ chart with the following context:
{context_info}

Please provide your analysis following the JSON format specified in the system prompt."""

    def _call_mistral_client(self, image_b64: str, context_prompt: str) -> str:
        """Call Mistral API using official client."""
        if not self.client:
            raise ValueError("Mistral client not available")
            
        try:
            messages = [
                {
                    "role": "system",
                    "content": self.system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": context_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": f"data:image/png;base64,{image_b64}"
                        }
                    ]
                }
            ]
            
            response = self.client.chat.complete(
                model=self.model,
                messages=messages,
                max_tokens=1000,
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            if content is None:
                return ""
            # Handle different content types
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                # Extract text from ContentChunk list
                text_parts = []
                for chunk in content:
                    # Handle different chunk types from Mistral API
                    if TextChunk is not None and isinstance(chunk, TextChunk):
                        if hasattr(chunk, 'text'):
                            text_parts.append(getattr(chunk, 'text'))
                    elif hasattr(chunk, 'text'):
                        text_value = getattr(chunk, 'text', None)
                        if text_value is not None:
                            text_parts.append(text_value)
                    elif hasattr(chunk, 'content'):
                        content_value = getattr(chunk, 'content', None)
                        if content_value is not None:
                            text_parts.append(content_value)
                    elif hasattr(chunk, 'data'):
                        data_value = getattr(chunk, 'data', None)
                        if data_value is not None:
                            text_parts.append(str(data_value))
                    else:
                        # Fallback for other chunk types that might contain text
                        chunk_str = str(chunk)
                        if chunk_str and chunk_str != str(type(chunk)):
                            text_parts.append(chunk_str)
                return ' '.join(text_parts)
            else:
                # Handle Unset or other types
                raise ValueError(f"Unexpected content type: {type(content)}")
                # Handle Unset or other types
                raise ValueError(f"Unexpected content type: {type(content)}")
            
        except Exception as e:
            logger.error(f"Mistral API call failed: {e}")
            raise
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from Mistral API."""
        try:
            # Try to extract JSON from response
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            response = response.strip()
            
            parsed = json.loads(response)
            return parsed
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            # Fallback to text-based parsing
            return {
                'summary': response[:200] + "..." if len(response) > 200 else response,
                'key_findings': [],
                'recommendations': [],
                'compliance_assessment': 'Unable to assess',
                'confidence': 0.5
            }
    
    def _create_fallback_analysis(self, chart_path: Path, chart_context: Dict[str, Any], 
                                 chart_type: str) -> GraphAnalysis:
        """Create a basic analysis when AI is not available."""
        parameter = chart_context.get('parameter', 'environmental parameter')
        room_id = chart_context.get('room_id', 'the monitored space')
        
        fallback_commentary = f"Chart shows {parameter} data for {room_id}. " \
                            f"Manual review recommended for detailed analysis."
        
        return GraphAnalysis(
            chart_name=chart_path.stem,
            chart_type=chart_type,
            ai_commentary=fallback_commentary,
            confidence_score=0.0,
            key_insights=["Manual analysis required"],
            suggested_actions=["Review chart manually", "Consult IEQ standards"],
            data_context=chart_context
        )

    def batch_analyze(self, chart_paths: List[Path], chart_contexts: List[Dict[str, Any]],
                     chart_types: Optional[List[str]] = None) -> Dict[str, GraphAnalysis]:
        """
        Analyze multiple charts in batch.
        
        Args:
            chart_paths: List of paths to chart files
            chart_contexts: List of context dictionaries for each chart
            chart_types: Optional list of chart types
            
        Returns:
            Dictionary mapping chart names to GraphAnalysis objects
        """
        if chart_types is None:
            chart_types = ["time_series"] * len(chart_paths)
            
        if len(chart_paths) != len(chart_contexts):
            raise ValueError("Number of chart paths must match number of contexts")
            
        results = {}
        
        for i, (chart_path, context, chart_type) in enumerate(zip(chart_paths, chart_contexts, chart_types)):
            logger.info(f"Analyzing chart {i+1}/{len(chart_paths)}: {chart_path.name}")
            
            analysis = self.analyze_chart(chart_path, context, chart_type)
            results[chart_path.stem] = analysis
            
        return results


class InteractiveReviewSystem:
    """Interactive system for reviewing AI-generated chart commentaries."""
    
    def __init__(self):
        self.reviewed_analyses: List[GraphAnalysis] = []
    
    def review_analysis(self, analysis: GraphAnalysis, chart_path: Path) -> GraphAnalysis:
        """
        Interactive review of AI-generated analysis.
        
        Args:
            analysis: AI-generated analysis to review
            chart_path: Path to chart image for reference
            
        Returns:
            Updated analysis with user feedback
        """
        print(f"\n{'='*80}")
        print(f"REVIEWING AI ANALYSIS FOR: {analysis.chart_name}")
        print(f"Chart Type: {analysis.chart_type}")
        print(f"Chart Path: {chart_path}")
        print(f"{'='*80}")
        
        # Display image info (in terminal we can't show the actual image)
        print(f"\n📊 Chart Image: {chart_path}")
        if chart_path.exists():
            file_size = chart_path.stat().st_size
            print(f"   File Size: {file_size:,} bytes")
            print(f"   Last Modified: {datetime.fromtimestamp(chart_path.stat().st_mtime)}")
        
        # Display AI analysis
        self._display_analysis(analysis)
        
        # Get user choice
        choice = self._get_user_choice()
        
        if choice == 'accept':
            analysis.reviewed = True
            analysis.final_commentary = analysis.ai_commentary
            print("✅ Analysis accepted as-is")
            
        elif choice == 'edit':
            analysis = self._edit_analysis(analysis)
            analysis.reviewed = True
            print("✅ Analysis updated with your changes")
            
        elif choice == 'reject':
            analysis = self._reject_analysis(analysis)
            analysis.reviewed = True
            print("❌ Analysis rejected - using fallback")
            
        self.reviewed_analyses.append(analysis)
        return analysis
    
    def _display_analysis(self, analysis: GraphAnalysis):
        """Display the AI analysis for review."""
        print(f"\n🤖 AI ANALYSIS (Confidence: {analysis.confidence_score:.2f})")
        print(f"{'─' * 60}")
        
        print(f"\n📝 SUMMARY:")
        print(f"   {analysis.ai_commentary}")
        
        if analysis.key_insights:
            print(f"\n💡 KEY INSIGHTS:")
            for i, insight in enumerate(analysis.key_insights, 1):
                print(f"   {i}. {insight}")
        
        if analysis.suggested_actions:
            print(f"\n🎯 SUGGESTED ACTIONS:")
            for i, action in enumerate(analysis.suggested_actions, 1):
                print(f"   {i}. {action}")
        
        print(f"\n📋 CONTEXT:")
        for key, value in analysis.data_context.items():
            print(f"   {key}: {value}")
    
    def _get_user_choice(self) -> str:
        """Get user choice for how to handle the analysis."""
        while True:
            print(f"\n❓ What would you like to do?")
            print(f"   [A]ccept - Use AI analysis as-is")
            print(f"   [E]dit - Modify the analysis")
            print(f"   [R]eject - Reject and use fallback")
            
            choice = input("Enter your choice (A/E/R): ").lower().strip()
            
            if choice in ['a', 'accept']:
                return 'accept'
            elif choice in ['e', 'edit']:
                return 'edit'
            elif choice in ['r', 'reject']:
                return 'reject'
            else:
                print("❌ Invalid choice. Please enter A, E, or R.")
    
    def _edit_analysis(self, analysis: GraphAnalysis) -> GraphAnalysis:
        """Allow user to edit the analysis."""
        print(f"\n✏️  EDITING ANALYSIS")
        print(f"Current summary: {analysis.ai_commentary}")
        
        new_summary = input("\nEnter new summary (or press Enter to keep current): ").strip()
        if new_summary:
            analysis.ai_commentary = new_summary
            analysis.final_commentary = new_summary
        
        # Edit insights
        print(f"\nCurrent insights: {len(analysis.key_insights)} items")
        edit_insights = input("Edit insights? (y/n): ").lower().strip()
        if edit_insights == 'y':
            new_insights = []
            print("Enter new insights (one per line, empty line to finish):")
            while True:
                insight = input("  - ").strip()
                if not insight:
                    break
                new_insights.append(insight)
            if new_insights:
                analysis.key_insights = new_insights
        
        # Edit actions
        print(f"\nCurrent actions: {len(analysis.suggested_actions)} items")
        edit_actions = input("Edit actions? (y/n): ").lower().strip()
        if edit_actions == 'y':
            new_actions = []
            print("Enter new actions (one per line, empty line to finish):")
            while True:
                action = input("  - ").strip()
                if not action:
                    break
                new_actions.append(action)
            if new_actions:
                analysis.suggested_actions = new_actions
        
        return analysis
    
    def _reject_analysis(self, analysis: GraphAnalysis) -> GraphAnalysis:
        """Handle rejection of AI analysis."""
        reason = input("\nOptional: Why are you rejecting this analysis? ").strip()
        
        # Create fallback analysis
        analysis.ai_commentary = f"AI analysis rejected by user. Manual review required."
        analysis.final_commentary = analysis.ai_commentary
        analysis.key_insights = ["Manual analysis required"]
        analysis.suggested_actions = ["Review chart manually", "Consult domain expert"]
        analysis.confidence_score = 0.0
        
        if reason:
            analysis.data_context['rejection_reason'] = reason
        
        return analysis
    
    def get_review_summary(self) -> Dict[str, Any]:
        """Get summary of all reviewed analyses."""
        total = len(self.reviewed_analyses)
        if total == 0:
            return {"total": 0, "summary": "No analyses reviewed yet"}
        
        accepted = sum(1 for a in self.reviewed_analyses if a.confidence_score > 0.5)
        rejected = sum(1 for a in self.reviewed_analyses if a.confidence_score == 0.0)
        edited = total - accepted - rejected
        
        return {
            "total": total,
            "accepted": accepted,
            "edited": edited,
            "rejected": rejected,
            "average_confidence": sum(a.confidence_score for a in self.reviewed_analyses) / total
        }


def validate_ai_setup() -> Tuple[bool, str]:
    """Validate that AI analysis setup is working correctly."""
    # Ensure .env is loaded
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    if not MISTRAL_AVAILABLE:
        return False, "Mistral AI package not installed. Run: pip install mistralai"
    
    api_key = os.getenv('MISTRAL_API_KEY')
    if not api_key:
        return False, "MISTRAL_API_KEY environment variable not set"
    
    # Try to create analyzer
    try:
        analyzer = AIGraphAnalyzer(api_key=api_key)
        if analyzer.client is None:
            return False, "Failed to create Mistral client"
        return True, "AI analysis setup is valid"
    except Exception as e:
        return False, f"Error creating AI analyzer: {e}"


# Helper functions for easy setup and testing
def create_ai_analyzer_with_config() -> AIGraphAnalyzer:
    """Create an AI analyzer with configuration from environment or config files."""
    # Try to load API key from environment
    api_key = os.getenv('MISTRAL_API_KEY')
    if api_key:
        return AIGraphAnalyzer(api_key=api_key)
    else:
        # Fallback to analyzer without API key (will use fallback analysis)
        return AIGraphAnalyzer()


if __name__ == "__main__":
    # Quick test when run directly
    is_valid, message = validate_ai_setup()
    print(f"AI Setup Status: {message}")
    
    if is_valid:
        print("✅ AI analysis is ready to use")
    else:
        print("❌ AI analysis setup incomplete")
        print("To enable AI analysis:")
        print("1. Install mistralai: pip install mistralai")
        print("2. Set environment variable: export MISTRAL_API_KEY=your_key_here")
        print("3. Or create .env file with: MISTRAL_API_KEY=your_key_here")
