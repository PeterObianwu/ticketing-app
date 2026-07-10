document.addEventListener('DOMContentLoaded', () => {
    // -----------------------------------------------------------------------
    // Session Key — a UUID stored in localStorage that identifies this browser.
    // It is sent with every API request so the backend scopes results to this
    // session only. Customers never see other users' tickets.
    // -----------------------------------------------------------------------
    function getOrCreateSessionKey() {
        let key = localStorage.getItem('ticket_session_key');
        if (!key) {
            // Use crypto.randomUUID if available (modern browsers), else fallback
            if (typeof crypto !== 'undefined' && crypto.randomUUID) {
                key = crypto.randomUUID();
            } else {
                key = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                    var r = Math.random() * 16 | 0;
                    var v = c === 'x' ? r : (r & 0x3 | 0x8);
                    return v.toString(16);
                });
            }
            localStorage.setItem('ticket_session_key', key);
        }
        return key;
    }

    var SESSION_KEY = getOrCreateSessionKey();

    // API Endpoints
    var API_URL = '/api/tickets/';

    // State Variables
    var allTickets = [];
    var currentFilter = 'all';
    var currentSearch = '';
    var currentSort = 'newest';

    // DOM Elements — guard against null to avoid fatal errors
    var ticketsGrid   = document.getElementById('tickets-grid');
    var openModalBtn  = document.getElementById('open-modal-btn');
    var closeModalBtn = document.getElementById('close-modal-btn');
    var cancelBtn     = document.getElementById('cancel-btn');
    var ticketModal   = document.getElementById('ticket-modal');
    var ticketForm    = document.getElementById('ticket-form');
    var modalTitle    = document.getElementById('modal-title');
    var searchInput   = document.getElementById('search-input');
    var sortSelect    = document.getElementById('sort-select');
    var filterButtons = document.querySelectorAll('.filter-btn');
    var statCards     = document.querySelectorAll('.stat-card');
    var toastContainer = document.getElementById('toast-container');

    // Stats Elements
    var statTotal    = document.getElementById('stat-total');
    var statOpen     = document.getElementById('stat-open');
    var statProgress = document.getElementById('stat-progress');
    var statResolved = document.getElementById('stat-resolved');

    // -----------------------------------------------------------------------
    // API Helpers
    // -----------------------------------------------------------------------
    function getCSRFToken() {
        var name = 'csrftoken';
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue || '';
    }

    function apiHeaders() {
        return {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
            'X-Session-Key': SESSION_KEY,
        };
    }

    // -----------------------------------------------------------------------
    // Modal Control — exposed on window so inline onclick can also call it
    // -----------------------------------------------------------------------
    function openModal() {
        if (!ticketModal || !ticketForm) return;
        ticketForm.reset();
        if (modalTitle) modalTitle.textContent = 'Submit Support Ticket';
        // Reset priority default
        var priorityEl = document.getElementById('priority');
        if (priorityEl) priorityEl.value = 'medium';
        ticketModal.classList.add('active');
        document.body.style.overflow = 'hidden';
        setTimeout(function() {
            var nameEl = document.getElementById('name');
            if (nameEl) nameEl.focus();
        }, 100);
    }
    window.openTicketModal = openModal; // expose for fallback

    function closeModal() {
        if (!ticketModal) return;
        ticketModal.classList.remove('active');
        document.body.style.overflow = '';
    }
    window.closeTicketModal = closeModal; // expose for fallback

    // -----------------------------------------------------------------------
    // Event Listeners
    // -----------------------------------------------------------------------
    if (openModalBtn)  openModalBtn.addEventListener('click', openModal);
    if (closeModalBtn) closeModalBtn.addEventListener('click', closeModal);
    if (cancelBtn)     cancelBtn.addEventListener('click', closeModal);

    if (ticketModal) {
        ticketModal.addEventListener('click', function(e) {
            if (e.target === ticketModal) closeModal();
        });
    }

    if (ticketForm) {
        ticketForm.addEventListener('submit', handleFormSubmit);
    }

    if (searchInput) {
        var searchTimeout = null;
        searchInput.addEventListener('input', function(e) {
            currentSearch = e.target.value;
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(fetchTickets, 300);
        });
    }

    if (sortSelect) {
        sortSelect.addEventListener('change', function(e) {
            currentSort = e.target.value;
            fetchTickets();
        });
    }

    filterButtons.forEach(function(btn) {
        btn.addEventListener('click', function() {
            filterButtons.forEach(function(b) { b.classList.remove('active'); });
            btn.classList.add('active');
            currentFilter = btn.dataset.filter;
            updateActiveFilterUI(currentFilter);
            fetchTickets();
        });
    });

    statCards.forEach(function(card) {
        card.addEventListener('click', function() {
            currentFilter = card.dataset.status;
            filterButtons.forEach(function(b) {
                b.classList.toggle('active', b.dataset.filter === currentFilter);
            });
            updateActiveFilterUI(currentFilter);
            fetchTickets();
        });
    });

    function updateActiveFilterUI(filter) {
        statCards.forEach(function(c) {
            if (c.dataset.status === filter) {
                c.style.borderColor = 'var(--primary)';
                c.style.boxShadow = '0 10px 25px -5px rgba(0,0,0,0.3), 0 0 15px 0 var(--panel-glow)';
            } else {
                c.style.borderColor = '';
                c.style.boxShadow = '';
            }
        });
    }

    // Initialize Page
    fetchTickets();

    // -----------------------------------------------------------------------
    // Core API Functions
    // -----------------------------------------------------------------------
    function fetchStats() {
        fetch(API_URL + 'stats/', {
            headers: { 'X-Session-Key': SESSION_KEY },
        })
        .then(function(response) {
            if (!response.ok) throw new Error('Failed to fetch stats');
            return response.json();
        })
        .then(function(stats) {
            if (statTotal)    statTotal.textContent    = stats.total;
            if (statOpen)     statOpen.textContent     = stats.open;
            if (statProgress) statProgress.textContent = stats.in_progress;
            if (statResolved) statResolved.textContent = stats.resolved;
        })
        .catch(function(error) {
            console.error('Failed to fetch stats:', error);
        });
    }

    function fetchTickets() {
        var url = new URL(API_URL, window.location.origin);
        if (currentFilter && currentFilter !== 'all') {
            url.searchParams.append('status', currentFilter);
        }
        if (currentSearch.trim() !== '') {
            url.searchParams.append('search', currentSearch);
        }
        if (currentSort) {
            url.searchParams.append('ordering', currentSort);
        }

        fetch(url.toString(), {
            headers: { 'X-Session-Key': SESSION_KEY },
        })
        .then(function(response) {
            if (!response.ok) throw new Error('Failed to fetch tickets');
            return response.json();
        })
        .then(function(data) {
            allTickets = data;
            fetchStats();
            renderTickets();
        })
        .catch(function(error) {
            console.error(error);
            showToast('Could not load tickets. Please try again.', 'error');
            if (ticketsGrid) {
                ticketsGrid.innerHTML =
                    '<div class="empty-state">' +
                    '<i class="fa-solid fa-circle-exclamation" style="color: var(--color-high)"></i>' +
                    '<p>Failed to connect to the backend server.</p>' +
                    '</div>';
            }
        });
    }

    function renderTickets() {
        if (!ticketsGrid) return;
        if (allTickets.length === 0) {
            ticketsGrid.innerHTML =
                '<div class="empty-state">' +
                '<i class="fa-solid fa-folder-open"></i>' +
                '<p>No tickets yet. Click <strong>New Ticket</strong> to submit one.</p>' +
                '</div>';
            return;
        }
        ticketsGrid.innerHTML = allTickets.map(createTicketCardHTML).join('');
    }

    // -----------------------------------------------------------------------
    // Ticket Card — read-only for customers
    // -----------------------------------------------------------------------
    function createTicketCardHTML(ticket) {
        var dateStr = new Date(ticket.created_at).toLocaleDateString(undefined, {
            month: 'short', day: 'numeric', year: 'numeric',
        });

        var statusLabels = { open: 'Open', in_progress: 'In Progress', resolved: 'Resolved' };
        var statusBadgeClass = 'badge-' + (ticket.status === 'in_progress' ? 'progress' : ticket.status);

        var locationHTML = ticket.location
            ? '<span class="card-location"><i class="fa-solid fa-location-dot"></i> ' + escapeHTML(ticket.location) + '</span>'
            : '';
        var nameHTML = ticket.name
            ? '<span class="card-name"><i class="fa-solid fa-user"></i> ' + escapeHTML(ticket.name) + '</span>'
            : '';

        return (
            '<div class="ticket-card status-' + ticket.status + '" data-id="' + ticket.id + '">' +
                '<div class="card-header">' +
                    '<h3 class="ticket-title">' + escapeHTML(ticket.title) + '</h3>' +
                    '<span class="badge ' + statusBadgeClass + '">' + (statusLabels[ticket.status] || ticket.status) + '</span>' +
                '</div>' +
                '<p class="ticket-desc">' + escapeHTML(ticket.description || 'No description provided.') + '</p>' +
                '<div class="card-meta">' + nameHTML + locationHTML + '</div>' +
                '<div class="card-details">' +
                    '<span class="card-priority priority-' + ticket.priority + '">' +
                        '<i class="fa-solid fa-circle" style="font-size:0.5rem"></i> ' + capitalize(ticket.priority) +
                    '</span>' +
                    '<span class="card-date">' + dateStr + '</span>' +
                '</div>' +
                '<div class="card-footer-note">' +
                    '<i class="fa-solid fa-lock" style="font-size:0.7rem"></i>' +
                    '<span>Status managed by admin</span>' +
                '</div>' +
            '</div>'
        );
    }

    // -----------------------------------------------------------------------
    // Create Ticket
    // -----------------------------------------------------------------------
    function handleFormSubmit(e) {
        e.preventDefault();

        var submitBtn = document.getElementById('submit-btn');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Submitting...';
        }

        var ticketData = {
            title:       (document.getElementById('title')       || {}).value || '',
            name:        (document.getElementById('name')        || {}).value || '',
            location:    (document.getElementById('location')    || {}).value || '',
            description: (document.getElementById('description') || {}).value || '',
            priority:    (document.getElementById('priority')    || {}).value || 'medium',
        };

        fetch(API_URL, {
            method: 'POST',
            headers: apiHeaders(),
            body: JSON.stringify(ticketData),
        })
        .then(function(response) {
            if (!response.ok) throw new Error('API Request Failed');
            showToast('Ticket submitted successfully!', 'success');
            closeModal();
            fetchTickets();
        })
        .catch(function(error) {
            console.error(error);
            showToast('Error submitting ticket. Please try again.', 'error');
        })
        .finally(function() {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Submit Ticket';
            }
        });
    }

    // -----------------------------------------------------------------------
    // Toast Notifications
    // -----------------------------------------------------------------------
    function showToast(message, type) {
        type = type || 'success';
        if (!toastContainer) return;
        var toast = document.createElement('div');
        toast.className = 'toast toast-' + type;
        var icon = type === 'success' ? 'fa-circle-check' : 'fa-circle-exclamation';
        toast.innerHTML = '<i class="fa-solid ' + icon + '"></i><span>' + message + '</span>';
        toastContainer.appendChild(toast);
        setTimeout(function() {
            toast.style.animation = 'fadeOut 0.3s ease forwards';
            toast.addEventListener('animationend', function() { toast.remove(); });
        }, 3500);
    }

    // -----------------------------------------------------------------------
    // Helpers
    // -----------------------------------------------------------------------
    function capitalize(string) {
        return string.charAt(0).toUpperCase() + string.slice(1).replace('_', ' ');
    }

    function escapeHTML(str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
});
