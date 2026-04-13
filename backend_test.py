import requests
import sys
import json
from datetime import datetime, timezone

class CognitiveOffloadingAPITester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_resources = {}  # Store created resource IDs for cleanup

    def run_test(self, name, method, endpoint, expected_status=200, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_base}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   {method} {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Response text: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_endpoints(self):
        """Test health and root endpoints"""
        print("\n🏥 Testing Health Endpoints")
        self.run_test("API Root", "GET", "", 200)
        self.run_test("Health Check", "GET", "health", 200)

    def test_experiment_crud(self):
        """Test experiment CRUD operations"""
        print("\n🧪 Testing Experiment CRUD")
        
        # Create experiment
        exp_data = {
            "name": "Test JIT Experiment",
            "description": "Testing Just-in-Time notification strategy",
            "config": {
                "notification_strategy": "just_in_time",
                "notification_frequency_minutes": 30,
                "blackout_duration_minutes": 60,
                "total_duration_minutes": 180,
                "time_compression_factor": 60.0,
                "num_doses": 3
            }
        }
        
        success, exp_response = self.run_test("Create Experiment", "POST", "experiments", 200, exp_data)
        if success and 'id' in exp_response:
            exp_id = exp_response['id']
            self.created_resources['experiment'] = exp_id
            
            # Get experiment by ID
            self.run_test("Get Experiment by ID", "GET", f"experiments/{exp_id}", 200)
            
            # Update experiment
            update_data = {
                "name": "Updated Test Experiment",
                "description": "Updated description",
                "config": exp_data["config"]
            }
            self.run_test("Update Experiment", "PUT", f"experiments/{exp_id}", 200, update_data)
        
        # Get all experiments
        self.run_test("Get All Experiments", "GET", "experiments", 200)
        
        # Test with filters
        self.run_test("Get Active Experiments", "GET", "experiments", 200, params={"is_active": True})

    def test_demographics_and_offloading(self):
        """Test participant demographics and offloading events - KEY THESIS FEATURES"""
        print("\n👤 Testing Demographics & Offloading Events")
        
        if 'experiment' not in self.created_resources:
            print("⚠️  Skipping demographics tests - no experiment available")
            return
        
        exp_id = self.created_resources['experiment']
        
        # Create participant with comprehensive demographics (THESIS REQUIREMENT)
        participant_data = {
            "participant_code": f"P{int(datetime.now().timestamp())}",
            "experiment_id": exp_id,
            "demographics": {
                "age_group": "25-34",
                "education": "masters", 
                "tech_familiarity": "often",
                "gender": "other",
                "occupation": "student",
                "memory_self_rating": 4,
                "reminder_app_usage": "daily",
                "health_condition_management": True
            }
        }
        
        success, participant_response = self.run_test("Create Participant with Demographics", "POST", "participants", 200, participant_data)
        if success and 'id' in participant_response:
            participant_id = participant_response['id']
            self.created_resources['participant'] = participant_id
            
            # Verify demographics were saved
            print("   📊 Verifying demographics saved to MongoDB...")
            success_get, get_response = self.run_test("Get Participant Demographics", "GET", f"participants/{participant_id}", 200)
            if success_get and 'demographics' in get_response:
                demographics = get_response['demographics']
                if demographics.get('age_group') == '25-34' and demographics.get('memory_self_rating') == 4:
                    print("   ✅ Demographics correctly saved to DB")
                else:
                    print("   ❌ Demographics not properly saved")
            
            # Create session for offloading tests
            session_data = {
                "participant_id": participant_id,
                "experiment_id": exp_id
            }
            
            success, session_response = self.run_test("Create Session", "POST", "sessions", 200, session_data)
            if success and 'id' in session_response:
                session_id = session_response['id']
                self.created_resources['session'] = session_id
                
                # Start session
                self.run_test("Start Session", "POST", f"sessions/{session_id}/start", 200)

    def test_offloading_mechanism(self):
        """Test offloading choice mechanism - CORE THESIS FEATURE"""
        print("\n🧠 Testing Offloading Choice Mechanism")
        
        if 'session' not in self.created_resources:
            print("⚠️  Skipping offloading tests - no session available")
            return
        
        session_id = self.created_resources['session']
        
        # Test "Remember" choice
        offloading_event_remember = {
            "notification_id": f"notif-{int(datetime.now().timestamp())}",
            "dose_number": 1,
            "choice": "remember",  # User chose to rely on internal memory
            "decision_time_ms": 1250,
            "notification_prominence": 1.0,
            "current_interval_minutes": 30.0
        }
        
        success_remember = self.run_test("Record Offloading Event - Remember Choice", "POST", f"sessions/{session_id}/offloading-event", 200, offloading_event_remember)
        
        # Test "Set Reminder" choice 
        offloading_event_reminder = {
            "notification_id": f"notif-{int(datetime.now().timestamp()) + 1}",
            "dose_number": 2,
            "choice": "set_reminder",  # User chose to offload to external system
            "decision_time_ms": 890,
            "notification_prominence": 0.85,  # For faded strategy
            "current_interval_minutes": 45.0  # For scaffolded strategy
        }
        
        success_reminder = self.run_test("Record Offloading Event - Set Reminder Choice", "POST", f"sessions/{session_id}/offloading-event", 200, offloading_event_reminder)
        
        if success_remember and success_reminder:
            print("   ✅ Both offloading choices (remember/set_reminder) working")
        else:
            print("   ❌ Offloading mechanism has issues")

    def test_response_time_tracking(self):
        """Test response time tracking for recall probes"""
        print("\n⏱️  Testing Response Time Tracking")
        
        if 'session' not in self.created_resources:
            print("⚠️  Skipping response time tests - no session available")
            return
            
        session_id = self.created_resources['session']
        
        # Record recall probe with precise response time (THESIS REQUIREMENT)
        probe_data = {
            "probe_type": "dose_number",
            "probe_time": datetime.now(timezone.utc).isoformat(),
            "probe_shown_timestamp": datetime.now(timezone.utc).isoformat(),
            "dose_asked": 1,
            "correct_answer": "1",
            "user_answer": "1", 
            "is_correct": True,
            "response_time_ms": 2847,  # Exact millisecond timing
            "response_submitted_timestamp": datetime.now(timezone.utc).isoformat(),
            "confidence_rating": 4
        }
        
        success = self.run_test("Record Recall Probe with Response Time", "POST", f"sessions/{session_id}/recall-probe", 200, probe_data)
        
        if success:
            print("   ✅ Response time tracking working (thesis critical)")
        else:
            print("   ❌ Response time tracking failed")

    def test_thesis_analytics_endpoints(self):
        """Test analytics endpoints critical for thesis"""
        print("\n📊 Testing Thesis Analytics Endpoints")
        
        # Test offloading comparison endpoint (KEY FOR THESIS)
        success, comparison_data = self.run_test("Get Offloading Comparison - Thesis Data", "GET", "analytics/offloading-comparison", 200)
        
        if success and 'comparison' in comparison_data:
            print("   ✅ Offloading comparison endpoint working")
            print(f"   📈 Found {len(comparison_data['comparison'])} strategy comparisons")
        else:
            print("   ❌ Offloading comparison endpoint failed")
        
        # Test full research data export
        success, export_data = self.run_test("Export Full Research Data - Thesis Export", "GET", "export/full-research-data", 200)
        
        if success and 'experiments' in export_data:
            print("   ✅ Full data export working")
            print(f"   📁 Export contains {len(export_data['experiments'])} experiments")
        else:
            print("   ❌ Full data export failed")

    def test_experiment_with_thesis_features(self):
        """Test experiment creation with scaffolded/faded strategy config"""
        print("\n🧪 Testing Experiment with Thesis-Specific Features")
        
        # Test scaffolded strategy experiment
        scaffolded_exp = {
            "name": "Scaffolded Strategy Test",
            "description": "Testing scaffolded reminders with increasing intervals",
            "config": {
                "notification_strategy": "scaffolded",
                "notification_frequency_minutes": 20,
                "blackout_duration_minutes": 90, 
                "total_duration_minutes": 240,
                "time_compression_factor": 120.0,
                "num_doses": 4,
                "scaffolded_increase_factor": 1.5,  # THESIS FEATURE
                "visual_persistence_seconds": 10
            }
        }
        
        success_scaffolded = self.run_test("Create Scaffolded Strategy Experiment", "POST", "experiments", 200, scaffolded_exp)
        
        # Test faded strategy experiment  
        faded_exp = {
            "name": "Faded Strategy Test",
            "description": "Testing faded reminders with decreasing opacity",
            "config": {
                "notification_strategy": "faded", 
                "notification_frequency_minutes": 25,
                "blackout_duration_minutes": 75,
                "total_duration_minutes": 200,
                "time_compression_factor": 80.0,
                "num_doses": 3,
                "faded_opacity_decay": 0.15,  # THESIS FEATURE
                "visual_persistence_seconds": 10
            }
        }
        
        success_faded = self.run_test("Create Faded Strategy Experiment", "POST", "experiments", 200, faded_exp)
        
        if success_scaffolded and success_faded:
            print("   ✅ Both scaffolded and faded strategy experiments created")
        else:
            print("   ❌ Issues with thesis-specific experiment features")

    def test_task_management(self):
        """Test task CRUD operations"""
        print("\n📋 Testing Task Management")
        
        # Create task
        task_data = {
            "title": "Test Task - Literature Review",
            "description": "Review cognitive offloading research papers",
            "week_number": 1,
            "priority": "p0",
            "target_date": "2026-01-15",
            "notes": "Focus on PM and digital notifications",
            "category": "Research"
        }
        
        success, task_response = self.run_test("Create Task", "POST", "tasks", 200, task_data)
        if success and 'id' in task_response:
            task_id = task_response['id']
            self.created_resources['task'] = task_id
            
            # Update task
            update_data = {
                "status": "completed",
                "actual_hours": 8.5,
                "notes": "Completed - reviewed 15 key papers"
            }
            self.run_test("Update Task", "PUT", f"tasks/{task_id}", 200, update_data)
            
            # Get task by ID
            self.run_test("Get Task by ID", "GET", f"tasks/{task_id}", 200)
        
        # Get all tasks
        self.run_test("Get All Tasks", "GET", "tasks", 200)
        
        # Get tasks with filters
        self.run_test("Get Tasks by Week", "GET", "tasks", 200, params={"week_number": 1})
        self.run_test("Get Tasks by Status", "GET", "tasks", 200, params={"status": "completed"})

    def test_weekly_reports(self):
        """Test weekly report functionality"""
        print("\n📝 Testing Weekly Reports")
        
        # Create weekly report
        report_data = {
            "week_number": 1,
            "start_date": "2026-01-06",
            "end_date": "2026-01-12",
            "summary": "Completed foundational research phase",
            "accomplishments": [
                "Reviewed 15 key papers on PM",
                "Defined 3 core research questions"
            ],
            "challenges": ["Large volume of literature to synthesize"],
            "next_week_goals": [
                "Design experiment protocol",
                "Create notification framework"
            ],
            "notes": "Good progress despite complexity"
        }
        
        success, report_response = self.run_test("Create Weekly Report", "POST", "weekly-reports", 200, report_data)
        if success and 'id' in report_response:
            report_id = report_response['id']
            self.created_resources['weekly_report'] = report_id
            
            # Update weekly report
            update_data = {
                **report_data,
                "summary": "Updated summary - research phase complete"
            }
            self.run_test("Update Weekly Report", "PUT", f"weekly-reports/{report_id}", 200, update_data)
            
            # Get report by ID
            self.run_test("Get Weekly Report by ID", "GET", f"weekly-reports/{report_id}", 200)
        
        # Get all weekly reports
        self.run_test("Get All Weekly Reports", "GET", "weekly-reports", 200)

    def test_analytics_endpoints(self):
        """Test analytics functionality"""
        print("\n📈 Testing Analytics")
        
        # Overview analytics
        self.run_test("Get Analytics Overview", "GET", "analytics/overview", 200)
        
        # Progress analytics
        self.run_test("Get Progress Analytics", "GET", "analytics/progress", 200)
        
        # Experiment analytics
        if 'experiment' in self.created_resources:
            exp_id = self.created_resources['experiment']
            self.run_test("Get Experiment Analytics", "GET", f"analytics/experiments/{exp_id}", 200)

    def test_export_functionality(self):
        """Test data export endpoints"""
        print("\n💾 Testing Export Functionality")
        
        # Export sessions (JSON)
        self.run_test("Export Sessions (JSON)", "GET", "export/sessions", 200, params={"format": "json"})
        
        # Export sessions (CSV)
        self.run_test("Export Sessions (CSV)", "GET", "export/sessions", 200, params={"format": "csv"})
        
        # Export tasks (JSON)
        self.run_test("Export Tasks (JSON)", "GET", "export/tasks", 200, params={"format": "json"})
        
        # Export tasks (CSV)  
        self.run_test("Export Tasks (CSV)", "GET", "export/tasks", 200, params={"format": "csv"})
        
        # Export weekly reports
        self.run_test("Export Weekly Reports (JSON)", "GET", "export/weekly-reports", 200, params={"format": "json"})

    def test_seed_data(self):
        """Test seed data endpoint"""
        print("\n🌱 Testing Seed Data")
        self.run_test("Seed Sample Data", "POST", "seed", 200)

    def cleanup_resources(self):
        """Clean up created test resources"""
        print("\n🧹 Cleaning up test resources...")
        
        # Delete in reverse order to handle dependencies
        if 'task' in self.created_resources:
            self.run_test("Delete Task", "DELETE", f"tasks/{self.created_resources['task']}", 200)
        
        if 'weekly_report' in self.created_resources:
            # Weekly reports don't have delete endpoint in the API
            pass
        
        if 'experiment' in self.created_resources:
            self.run_test("Delete Experiment", "DELETE", f"experiments/{self.created_resources['experiment']}", 200)

    def run_all_tests(self):
        """Run comprehensive API test suite"""
        print("🚀 Starting Cognitive Offloading Research Tool API Tests")
        print(f"🎯 Testing against: {self.base_url}")
        
        try:
            # Core functionality tests
            self.test_health_endpoints()
            self.test_experiment_with_thesis_features()
            self.test_experiment_crud()
            self.test_demographics_and_offloading()
            self.test_offloading_mechanism()
            self.test_response_time_tracking()
            self.test_thesis_analytics_endpoints()
            self.test_task_management()
            self.test_weekly_reports()
            self.test_analytics_endpoints()
            self.test_export_functionality()
            
            # Seed data test (optional - creates sample data)
            # self.test_seed_data()
            
        except KeyboardInterrupt:
            print("\n⚠️ Tests interrupted by user")
        except Exception as e:
            print(f"\n💥 Unexpected error: {str(e)}")
        finally:
            # Clean up
            self.cleanup_resources()
            
            # Print final results
            print(f"\n📊 Test Results:")
            print(f"   Tests Run: {self.tests_run}")
            print(f"   Tests Passed: {self.tests_passed}")
            print(f"   Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%" if self.tests_run > 0 else "No tests run")
            
            if self.tests_passed == self.tests_run:
                print("✅ All tests passed!")
                return 0
            else:
                print(f"❌ {self.tests_run - self.tests_passed} tests failed")
                return 1

def main():
    tester = CognitiveOffloadingAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())
