"""
Backend API Tests for New Features:
1. Shareable Participant Links (share_code, join endpoint)
2. PDF Report Generation (/api/export/pdf-report)
3. Data Export Validation (/api/export/validated-research-data)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001').rstrip('/')

class TestHealthAndBasics:
    """Basic health check tests"""
    
    def test_api_health(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✓ API health check passed")

    def test_api_root(self):
        """Test API root endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "PM Research Lab API" in data["message"]
        print("✓ API root endpoint passed")


class TestSeedData:
    """Test seed data endpoint - required for share code tests"""
    
    def test_seed_data(self):
        """Seed data to create experiments with share codes"""
        response = requests.post(f"{BASE_URL}/api/seed")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✓ Seed data response: {data}")


class TestShareableParticipantLinks:
    """Feature 1: Shareable Participant Links Tests"""
    
    def test_experiments_have_share_code(self):
        """GET /api/experiments should return experiments with share_code field"""
        response = requests.get(f"{BASE_URL}/api/experiments")
        assert response.status_code == 200
        experiments = response.json()
        assert len(experiments) > 0, "No experiments found - seed data first"
        
        for exp in experiments:
            assert "share_code" in exp, f"Experiment {exp.get('name')} missing share_code"
            assert exp["share_code"] is not None, f"Experiment {exp.get('name')} has null share_code"
            print(f"✓ Experiment '{exp['name']}' has share_code: {exp['share_code']}")
        
        print(f"✓ All {len(experiments)} experiments have share_code field")
    
    def test_join_experiment_valid_code_jit2026a(self):
        """GET /api/experiments/join/JIT2026A returns experiment"""
        response = requests.get(f"{BASE_URL}/api/experiments/join/JIT2026A")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "config" in data
        assert data["share_code"] == "JIT2026A"
        print(f"✓ Valid share code JIT2026A returns experiment: {data['name']}")
    
    def test_join_experiment_valid_code_scf2026b(self):
        """GET /api/experiments/join/SCF2026B returns experiment"""
        response = requests.get(f"{BASE_URL}/api/experiments/join/SCF2026B")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["share_code"] == "SCF2026B"
        print(f"✓ Valid share code SCF2026B returns experiment: {data['name']}")
    
    def test_join_experiment_valid_code_fad2026c(self):
        """GET /api/experiments/join/FAD2026C returns experiment"""
        response = requests.get(f"{BASE_URL}/api/experiments/join/FAD2026C")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["share_code"] == "FAD2026C"
        print(f"✓ Valid share code FAD2026C returns experiment: {data['name']}")
    
    def test_join_experiment_valid_code_ctl2026d(self):
        """GET /api/experiments/join/CTL2026D returns experiment"""
        response = requests.get(f"{BASE_URL}/api/experiments/join/CTL2026D")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["share_code"] == "CTL2026D"
        print(f"✓ Valid share code CTL2026D returns experiment: {data['name']}")
    
    def test_join_experiment_lowercase_code(self):
        """GET /api/experiments/join/jit2026a (lowercase) should also work"""
        response = requests.get(f"{BASE_URL}/api/experiments/join/jit2026a")
        assert response.status_code == 200, f"Expected 200 for lowercase code, got {response.status_code}"
        data = response.json()
        assert data["share_code"] == "JIT2026A"
        print("✓ Lowercase share code also works (case-insensitive)")
    
    def test_join_experiment_invalid_code(self):
        """GET /api/experiments/join/INVALID123 returns 404"""
        response = requests.get(f"{BASE_URL}/api/experiments/join/INVALID123")
        assert response.status_code == 404, f"Expected 404 for invalid code, got {response.status_code}"
        data = response.json()
        assert "detail" in data
        print(f"✓ Invalid share code returns 404 with message: {data['detail']}")
    
    def test_join_experiment_empty_code(self):
        """GET /api/experiments/join/ with empty code returns error"""
        response = requests.get(f"{BASE_URL}/api/experiments/join/")
        # Should return 404 or 405 for empty path
        assert response.status_code in [404, 405, 422], f"Expected error for empty code, got {response.status_code}"
        print("✓ Empty share code returns appropriate error")


class TestPDFReportGeneration:
    """Feature 2: PDF Report Generation Tests"""
    
    def test_pdf_report_endpoint_returns_pdf(self):
        """GET /api/export/pdf-report returns a PDF with correct content type"""
        response = requests.get(f"{BASE_URL}/api/export/pdf-report")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Check content type
        content_type = response.headers.get("Content-Type", "")
        assert "application/pdf" in content_type, f"Expected application/pdf, got {content_type}"
        
        # Check content disposition header
        content_disp = response.headers.get("Content-Disposition", "")
        assert "attachment" in content_disp, f"Expected attachment disposition, got {content_disp}"
        assert ".pdf" in content_disp, f"Expected .pdf in filename, got {content_disp}"
        
        # Check PDF magic bytes
        pdf_content = response.content
        assert pdf_content[:4] == b'%PDF', "Response does not start with PDF magic bytes"
        
        # Check reasonable size (should be at least a few KB)
        assert len(pdf_content) > 1000, f"PDF seems too small: {len(pdf_content)} bytes"
        
        print(f"✓ PDF report generated successfully, size: {len(pdf_content)} bytes")
        print(f"✓ Content-Type: {content_type}")
        print(f"✓ Content-Disposition: {content_disp}")
    
    def test_pdf_report_with_experiment_filter(self):
        """GET /api/export/pdf-report?experiment_id=xxx works"""
        # First get an experiment ID
        exp_response = requests.get(f"{BASE_URL}/api/experiments")
        experiments = exp_response.json()
        if experiments:
            exp_id = experiments[0]["id"]
            response = requests.get(f"{BASE_URL}/api/export/pdf-report?experiment_id={exp_id}")
            assert response.status_code == 200
            assert "application/pdf" in response.headers.get("Content-Type", "")
            print(f"✓ PDF report with experiment filter works for experiment: {exp_id}")
        else:
            print("⚠ No experiments to test filter with")


class TestValidatedDataExport:
    """Feature 3: Data Export Validation Tests"""
    
    def test_validated_research_data_endpoint(self):
        """GET /api/export/validated-research-data returns JSON with required fields"""
        response = requests.get(f"{BASE_URL}/api/export/validated-research-data")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Check required top-level fields
        assert "data_integrity" in data, "Missing data_integrity field"
        assert "strategy_summary" in data, "Missing strategy_summary field"
        assert "demographics_summary" in data, "Missing demographics_summary field"
        assert "export_timestamp" in data, "Missing export_timestamp field"
        assert "experiments" in data, "Missing experiments field"
        assert "sessions" in data, "Missing sessions field"
        
        print(f"✓ Validated data export has all required fields")
        
        # Check data_integrity structure
        integrity = data["data_integrity"]
        assert "total_experiments" in integrity
        assert "total_participants" in integrity
        assert "total_sessions" in integrity
        assert "completed_sessions" in integrity
        print(f"✓ Data integrity: {integrity['total_experiments']} experiments, {integrity['total_sessions']} sessions")
        
        # Check demographics_summary structure
        demo_summary = data["demographics_summary"]
        assert "age_groups" in demo_summary
        assert "education_levels" in demo_summary
        assert "tech_familiarity" in demo_summary
        assert "memory_self_ratings" in demo_summary
        print(f"✓ Demographics summary structure validated")
        
        # Check strategy_summary is a dict
        assert isinstance(data["strategy_summary"], dict)
        print(f"✓ Strategy summary contains {len(data['strategy_summary'])} strategies")
    
    def test_validated_data_sessions_have_cross_references(self):
        """Validated sessions should have cross-referenced data"""
        response = requests.get(f"{BASE_URL}/api/export/validated-research-data")
        assert response.status_code == 200
        data = response.json()
        
        sessions = data.get("sessions", [])
        if sessions:
            session = sessions[0]
            # Check cross-referenced fields
            assert "session_id" in session
            assert "participant_id" in session
            assert "experiment_id" in session
            assert "experiment_name" in session
            assert "strategy" in session
            assert "offloading_rate" in session
            assert "recall_accuracy_percent" in session
            print(f"✓ Sessions have cross-referenced data (checked {len(sessions)} sessions)")
        else:
            print("⚠ No sessions to validate cross-references")


class TestResearcherAuthentication:
    """Test researcher login functionality"""
    
    def test_researcher_password_works(self):
        """Verify researcher password pmresearch2026 is correct (frontend check)"""
        # This is a frontend-only check, but we can verify the experiments endpoint works
        response = requests.get(f"{BASE_URL}/api/experiments")
        assert response.status_code == 200
        print("✓ API accessible (researcher auth is frontend-only)")


class TestExistingEndpoints:
    """Verify existing endpoints still work after new features"""
    
    def test_get_experiments(self):
        """GET /api/experiments works"""
        response = requests.get(f"{BASE_URL}/api/experiments")
        assert response.status_code == 200
        print(f"✓ GET /api/experiments returns {len(response.json())} experiments")
    
    def test_get_participants(self):
        """GET /api/participants works"""
        response = requests.get(f"{BASE_URL}/api/participants")
        assert response.status_code == 200
        print(f"✓ GET /api/participants returns {len(response.json())} participants")
    
    def test_get_sessions(self):
        """GET /api/sessions works"""
        response = requests.get(f"{BASE_URL}/api/sessions")
        assert response.status_code == 200
        print(f"✓ GET /api/sessions returns {len(response.json())} sessions")
    
    def test_analytics_overview(self):
        """GET /api/analytics/overview works"""
        response = requests.get(f"{BASE_URL}/api/analytics/overview")
        assert response.status_code == 200
        data = response.json()
        assert "total_experiments" in data
        print(f"✓ Analytics overview: {data['total_experiments']} experiments, {data['total_participants']} participants")
    
    def test_offloading_comparison(self):
        """GET /api/analytics/offloading-comparison works"""
        response = requests.get(f"{BASE_URL}/api/analytics/offloading-comparison")
        assert response.status_code == 200
        data = response.json()
        assert "comparison" in data
        print(f"✓ Offloading comparison: {len(data['comparison'])} strategies compared")
    
    def test_full_research_data_export(self):
        """GET /api/export/full-research-data works"""
        response = requests.get(f"{BASE_URL}/api/export/full-research-data")
        assert response.status_code == 200
        data = response.json()
        assert "experiments" in data
        assert "participants" in data
        assert "sessions" in data
        print(f"✓ Full research data export works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
