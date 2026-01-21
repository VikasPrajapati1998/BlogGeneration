const API_BASE = '';
let currentBlogId = null;
let currentFilter = 'all';
let pollInterval = null;
let statsInterval = null;

// DOM Elements
const blogForm = document.getElementById('blogForm');
const topicInput = document.getElementById('topic');
const generateBtn = document.getElementById('generateBtn');
const loadingIndicator = document.getElementById('loadingIndicator');
const generatedBlog = document.getElementById('generatedBlog');
const blogsList = document.getElementById('blogsList');
const refreshBtn = document.getElementById('refreshBtn');
const rejectModal = document.getElementById('rejectModal');
const rejectionReason = document.getElementById('rejectionReason');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('Page loaded - initializing...');
    
    // CRITICAL: Ensure modal is hidden on page load
    if (rejectModal) {
        rejectModal.classList.add('hidden');
        rejectModal.style.display = 'none';
    }
    
    // Load initial data
    loadAllBlogs();
    loadStats();
    
    // Update stats every 30 seconds (reduced from 10 seconds)
    statsInterval = setInterval(loadStats, 30000);
    
    console.log('Initialization complete');
});

// Event Listeners
if (blogForm) {
    blogForm.addEventListener('submit', handleGenerate);
}

if (refreshBtn) {
    refreshBtn.addEventListener('click', () => {
        loadAllBlogs();
        loadStats();
    });
}

// Load statistics
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/api/stats`);
        if (!response.ok) throw new Error('Failed to load stats');
        
        const stats = await response.json();
        document.getElementById('totalBlogs').textContent = stats.total;
        document.getElementById('pendingBlogs').textContent = stats.pending;
        document.getElementById('approvedBlogs').textContent = stats.approved;
        document.getElementById('rejectedBlogs').textContent = stats.rejected;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Generate Blog
async function handleGenerate(e) {
    e.preventDefault();
    
    const topic = topicInput.value.trim();
    if (!topic) {
        alert('Please enter a blog topic');
        return;
    }
    
    console.log('Generating blog for topic:', topic);
    
    // Reset state
    currentBlogId = null;
    generateBtn.disabled = true;
    loadingIndicator.classList.remove('hidden');
    generatedBlog.classList.add('hidden');
    
    // Reset progress steps
    document.getElementById('step1').innerHTML = '✓ Researching topic...';
    document.getElementById('step2').innerHTML = '⏳ Creating title...';
    document.getElementById('step3').innerHTML = '⏳ Writing content...';
    document.getElementById('step4').innerHTML = '⏳ Editing & refining...';
    
    // Simulate progress steps
    simulateProgress();
    
    try {
        const response = await fetch(`${API_BASE}/api/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ topic })
        });
        
        if (!response.ok) {
            throw new Error('Failed to generate blog');
        }
        
        const blog = await response.json();
        console.log('Blog creation started, ID:', blog.id, 'Status:', blog.status);
        
        // Start polling for this specific blog
        startPollingBlog(blog.id);
        
        loadAllBlogs();
        loadStats();
        topicInput.value = '';
        
    } catch (error) {
        alert('Error generating blog: ' + error.message);
        console.error(error);
        generateBtn.disabled = false;
        loadingIndicator.classList.add('hidden');
    }
}

// Poll for blog updates - with completion detection
function startPollingBlog(blogId) {
    console.log('Starting to poll for blog:', blogId);
    
    // Clear any existing poll
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
    
    let pollCount = 0;
    const maxPolls = 150; // Maximum 5 minutes (150 * 2 seconds)
    
    // Poll every 2 seconds
    pollInterval = setInterval(async () => {
        pollCount++;
        
        // Timeout after max polls
        if (pollCount > maxPolls) {
            console.error('Polling timeout - blog generation took too long');
            clearInterval(pollInterval);
            pollInterval = null;
            generateBtn.disabled = false;
            loadingIndicator.classList.add('hidden');
            alert('Blog generation is taking longer than expected. Please refresh the page.');
            return;
        }
        
        try {
            const response = await fetch(`${API_BASE}/api/blogs/${blogId}`);
            if (!response.ok) {
                console.error('Failed to fetch blog status');
                clearInterval(pollInterval);
                pollInterval = null;
                generateBtn.disabled = false;
                loadingIndicator.classList.add('hidden');
                return;
            }
            
            const blog = await response.json();
            
            // Check if blog is still being generated
            if (blog.title === "Generating..." || blog.content === "Blog generation in progress...") {
                console.log(`Poll ${pollCount}: Still generating...`);
                return; // Keep polling
            }
            
            // Blog is ready!
            console.log('Blog generation complete!');
            console.log('Final status:', blog.status);
            
            // STOP polling immediately
            clearInterval(pollInterval);
            pollInterval = null;
            
            generateBtn.disabled = false;
            loadingIndicator.classList.add('hidden');
            
            displayGeneratedBlog(blog);
            loadAllBlogs();
            loadStats();
            
        } catch (error) {
            console.error('Error polling blog:', error);
        }
    }, 2000);
}

// Simulate progress animation
function simulateProgress() {
    const steps = ['step1', 'step2', 'step3', 'step4'];
    steps.forEach((step, index) => {
        setTimeout(() => {
            const el = document.getElementById(step);
            if (el) {
                el.style.color = '#667eea';
                if (index < steps.length - 1) {
                    const nextEl = document.getElementById(steps[index + 1]);
                    if (nextEl) {
                        nextEl.innerHTML = nextEl.innerHTML.replace('⏳', '✓');
                    }
                }
            }
        }, index * 3000);
    });
}

// Display generated blog
function displayGeneratedBlog(blog) {
    console.log('Displaying blog:', blog.id, blog.title, 'Status:', blog.status);
    
    // Set current blog ID
    currentBlogId = blog.id;
    
    // Update content
    document.getElementById('blogTitle').textContent = blog.title;
    document.getElementById('blogTopic').textContent = blog.topic;
    document.getElementById('blogContent').textContent = blog.content;
    
    // Update status badge
    const statusBadge = document.getElementById('generatedBlogStatus');
    statusBadge.textContent = blog.status.toUpperCase();
    statusBadge.className = `status-badge status-${blog.status}`;
    
    // IMPORTANT: Only show review actions for truly pending blogs (not generating)
    const reviewActions = document.getElementById('reviewActions');
    const isGenerating = blog.title === 'Generating...' || blog.content === 'Blog generation in progress...';
    
    if (blog.status === 'pending' && !isGenerating) {
        reviewActions.classList.remove('hidden');
        console.log('Showing approve/reject buttons');
    } else {
        reviewActions.classList.add('hidden');
        console.log('Hiding approve/reject buttons - status:', blog.status, 'isGenerating:', isGenerating);
    }
    
    // Show the blog section
    generatedBlog.classList.remove('hidden');
    generatedBlog.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Approve blog
async function approveBlog() {
    console.log('Approve clicked, currentBlogId:', currentBlogId);
    
    // Guard clause - ensure we have a valid blog ID
    if (!currentBlogId) {
        console.error('No blog selected for approval');
        alert('No blog selected. Please generate or select a blog first.');
        return;
    }
    
    if (!confirm('Are you sure you want to approve this blog?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/blogs/${currentBlogId}/review`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ action: 'approve' })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to approve blog');
        }
        
        const blog = await response.json();
        displayGeneratedBlog(blog);
        loadAllBlogs();
        loadStats();
        alert('Blog approved successfully! ✓');
        
    } catch (error) {
        alert('Error approving blog: ' + error.message);
        console.error(error);
    }
}

// Show reject modal - with validation
function showRejectModal() {
    console.log('showRejectModal called, currentBlogId:', currentBlogId);
    
    // Guard clause - ensure we have a valid blog ID
    if (!currentBlogId) {
        console.error('No blog selected for rejection');
        alert('No blog selected. Please generate or select a blog first.');
        return;
    }
    
    // Clear previous reason and show modal
    if (rejectionReason) {
        rejectionReason.value = '';
    }
    
    if (rejectModal) {
        rejectModal.classList.remove('hidden');
        rejectModal.style.display = 'flex';
        console.log('Modal displayed');
        
        // Focus on textarea
        if (rejectionReason) {
            rejectionReason.focus();
        }
    }
}

// Close reject modal
function closeRejectModal() {
    console.log('Closing modal');
    
    if (rejectModal) {
        rejectModal.classList.add('hidden');
        rejectModal.style.display = 'none';
    }
    
    if (rejectionReason) {
        rejectionReason.value = '';
    }
}

// Reject blog
async function rejectBlog() {
    console.log('Reject clicked, currentBlogId:', currentBlogId);
    
    // Guard clause
    if (!currentBlogId) {
        console.error('No blog selected for rejection');
        alert('No blog selected');
        closeRejectModal();
        return;
    }
    
    const reason = rejectionReason.value.trim();
    if (!reason) {
        alert('Please provide a rejection reason');
        if (rejectionReason) {
            rejectionReason.focus();
        }
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/blogs/${currentBlogId}/review`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                action: 'reject',
                rejection_reason: reason
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to reject blog');
        }
        
        const blog = await response.json();
        closeRejectModal();
        displayGeneratedBlog(blog);
        loadAllBlogs();
        loadStats();
        alert('Blog rejected successfully.');
        
    } catch (error) {
        alert('Error rejecting blog: ' + error.message);
        console.error(error);
    }
}

// Filter blogs
function filterBlogs(status) {
    currentFilter = status;
    
    // Update active tab
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    loadAllBlogs();
}

// Load all blogs
async function loadAllBlogs() {
    try {
        let url = `${API_BASE}/api/blogs`;
        if (currentFilter !== 'all') {
            url += `?status=${currentFilter}`;
        }
        
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error('Failed to load blogs');
        }
        
        const blogs = await response.json();
        displayBlogs(blogs);
        
    } catch (error) {
        console.error('Error loading blogs:', error);
        if (blogsList) {
            blogsList.innerHTML = '<p class="empty-state">Error loading blogs</p>';
        }
    }
}

// Display blogs list
function displayBlogs(blogs) {
    if (!blogsList) return;
    
    if (blogs.length === 0) {
        const filterText = currentFilter === 'all' ? '' : ` (${currentFilter})`;
        blogsList.innerHTML = `<p class="empty-state">No blogs found${filterText}.</p>`;
        return;
    }
    
    blogsList.innerHTML = blogs.map(blog => {
        const isGenerating = blog.title === 'Generating...' || blog.content === 'Blog generation in progress...';
        const canReview = blog.status === 'pending' && !isGenerating;
        
        return `
            <div class="blog-item">
                <div class="blog-item-header">
                    <h4>${escapeHtml(blog.title)}</h4>
                    <span class="status-badge status-${blog.status}">${blog.status.toUpperCase()}</span>
                </div>
                <div class="meta">
                    Topic: ${escapeHtml(blog.topic)} | 
                    Created: ${new Date(blog.created_at).toLocaleString()}
                    ${blog.approved_at ? ` | Approved: ${new Date(blog.approved_at).toLocaleString()}` : ''}
                </div>
                ${blog.rejection_reason ? `
                    <div class="rejection-reason">
                        <strong>Rejection Reason:</strong> ${escapeHtml(blog.rejection_reason)}
                    </div>
                ` : ''}
                <div class="preview">
                    ${escapeHtml(blog.content.substring(0, 200))}${blog.content.length > 200 ? '...' : ''}
                </div>
                <div class="actions">
                    <button class="btn btn-secondary" onclick="viewBlog(${blog.id})">
                        View Full
                    </button>
                    ${canReview ? `
                        <button class="btn btn-success" onclick="reviewBlogById(${blog.id}, 'approve')">
                            ✓ Approve
                        </button>
                        <button class="btn btn-warning" onclick="reviewBlogById(${blog.id}, 'reject')">
                            ✗ Reject
                        </button>
                    ` : ''}
                    <button class="btn btn-danger" onclick="deleteBlog(${blog.id})">
                        Delete
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// View full blog
async function viewBlog(id) {
    console.log('Viewing blog:', id);
    
    try {
        const response = await fetch(`${API_BASE}/api/blogs/${id}`);
        if (!response.ok) {
            throw new Error('Failed to load blog');
        }
        
        const blog = await response.json();
        displayGeneratedBlog(blog);
        
    } catch (error) {
        alert('Error loading blog: ' + error.message);
        console.error(error);
    }
}

// Review blog by ID
async function reviewBlogById(id, action) {
    console.log('Review blog by ID:', id, action);
    
    try {
        // First load the blog to display it
        await viewBlog(id);
        
        // Small delay to ensure currentBlogId is set
        await new Promise(resolve => setTimeout(resolve, 100));
        
        // Verify currentBlogId is set
        if (currentBlogId !== id) {
            console.error('Failed to set currentBlogId');
            return;
        }
        
        // Perform the action
        if (action === 'approve') {
            approveBlog();
        } else if (action === 'reject') {
            showRejectModal();
        }
    } catch (error) {
        console.error('Error in reviewBlogById:', error);
        alert('Error loading blog for review');
    }
}

// Delete blog
async function deleteBlog(id) {
    if (!confirm('Are you sure you want to delete this blog?')) {
        return;
    }
    
    try {
        // Stop polling if deleting current blog being generated
        if (pollInterval) {
            clearInterval(pollInterval);
            pollInterval = null;
        }
        
        const response = await fetch(`${API_BASE}/api/blogs/${id}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete blog');
        }
        
        // Hide generated blog if it was the one deleted
        if (currentBlogId === id) {
            if (generatedBlog) {
                generatedBlog.classList.add('hidden');
            }
            currentBlogId = null;
        }
        
        loadAllBlogs();
        loadStats();
        alert('Blog deleted successfully');
        
    } catch (error) {
        alert('Error deleting blog: ' + error.message);
        console.error(error);
    }
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Modal event handlers
if (rejectModal) {
    // Close modal when clicking outside
    rejectModal.addEventListener('click', function(event) {
        if (event.target === rejectModal) {
            closeRejectModal();
        }
    });
}

// Close modal on Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape' && rejectModal && !rejectModal.classList.contains('hidden')) {
        closeRejectModal();
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
    if (statsInterval) {
        clearInterval(statsInterval);
        statsInterval = null;
    }
});
