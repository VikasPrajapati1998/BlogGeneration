const API_BASE = '';

// DOM Elements
const blogForm = document.getElementById('blogForm');
const topicInput = document.getElementById('topic');
const generateBtn = document.getElementById('generateBtn');
const loadingIndicator = document.getElementById('loadingIndicator');
const generatedBlog = document.getElementById('generatedBlog');
const blogsList = document.getElementById('blogsList');
const refreshBtn = document.getElementById('refreshBtn');

// Event Listeners
blogForm.addEventListener('submit', handleGenerate);
refreshBtn.addEventListener('click', loadAllBlogs);

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadAllBlogs();
});

// Generate Blog
async function handleGenerate(e) {
    e.preventDefault();
    
    const topic = topicInput.value.trim();
    if (!topic) return;
    
    // Show loading
    generateBtn.disabled = true;
    loadingIndicator.classList.remove('hidden');
    generatedBlog.classList.add('hidden');
    
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
        displayGeneratedBlog(blog);
        loadAllBlogs();
        topicInput.value = '';
        
    } catch (error) {
        alert('Error generating blog: ' + error.message);
        console.error(error);
    } finally {
        generateBtn.disabled = false;
        loadingIndicator.classList.add('hidden');
    }
}

// Simulate progress animation
function simulateProgress() {
    const steps = ['step1', 'step2', 'step3', 'step4'];
    steps.forEach((step, index) => {
        setTimeout(() => {
            document.getElementById(step).style.color = '#667eea';
            if (index < steps.length - 1) {
                document.getElementById(steps[index + 1]).innerHTML = 
                    document.getElementById(steps[index + 1]).innerHTML.replace('⏳', '✓');
            }
        }, index * 3000);
    });
}

// Display generated blog
function displayGeneratedBlog(blog) {
    document.getElementById('blogTitle').textContent = blog.title;
    document.getElementById('blogTopic').textContent = blog.topic;
    document.getElementById('blogContent').textContent = blog.content;
    generatedBlog.classList.remove('hidden');
    generatedBlog.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Load all blogs
async function loadAllBlogs() {
    try {
        const response = await fetch(`${API_BASE}/api/blogs`);
        if (!response.ok) {
            throw new Error('Failed to load blogs');
        }
        
        const blogs = await response.json();
        displayBlogs(blogs);
        
    } catch (error) {
        console.error('Error loading blogs:', error);
        blogsList.innerHTML = '<p class="empty-state">Error loading blogs</p>';
    }
}

// Display blogs list
function displayBlogs(blogs) {
    if (blogs.length === 0) {
        blogsList.innerHTML = '<p class="empty-state">No blogs yet. Generate your first one!</p>';
        return;
    }
    
    blogsList.innerHTML = blogs.map(blog => `
        <div class="blog-item">
            <h4>${escapeHtml(blog.title)}</h4>
            <div class="meta">
                Topic: ${escapeHtml(blog.topic)} | 
                Created: ${new Date(blog.created_at).toLocaleString()}
            </div>
            <div class="preview">
                ${escapeHtml(blog.content.substring(0, 200))}...
            </div>
            <div class="actions">
                <button class="btn btn-secondary" onclick="viewBlog(${blog.id})">
                    View Full
                </button>
                <button class="btn btn-danger" onclick="deleteBlog(${blog.id})">
                    Delete
                </button>
            </div>
        </div>
    `).join('');
}

// View full blog
async function viewBlog(id) {
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

// Delete blog
async function deleteBlog(id) {
    if (!confirm('Are you sure you want to delete this blog?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/blogs/${id}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete blog');
        }
        
        loadAllBlogs();
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

