/**
 * Real-Time Cross-Role Sync Client (SSE EventSource)
 * Manages live pub/sub sync between Kitchen, Front Desk, Housekeeping, POS, and Guests.
 */
(function () {
  'use strict';

  let eventSource = null;
  let reconnectAttempts = 0;
  const maxReconnectDelay = 30000;

  function getMeta(name) {
    const el = document.querySelector(`meta[name="${name}"]`);
    return el ? el.getAttribute('content') : '';
  }

  function updateStatusIndicator(status) {
    const dot = document.getElementById('sync-status-dot');
    if (!dot) return;

    dot.classList.remove('status-connected', 'status-reconnecting', 'status-offline');
    if (status === 'connected') {
      dot.classList.add('status-connected');
      dot.setAttribute('title', 'Real-Time Sync: Connected');
      dot.style.backgroundColor = '#10b981'; // Green
    } else if (status === 'reconnecting') {
      dot.classList.add('status-reconnecting');
      dot.setAttribute('title', 'Real-Time Sync: Reconnecting...');
      dot.style.backgroundColor = '#f59e0b'; // Yellow
    } else {
      dot.classList.add('status-offline');
      dot.setAttribute('title', 'Real-Time Sync: Offline');
      dot.style.backgroundColor = '#ef4444'; // Red
    }
  }

  function determineChannels() {
    const role = getMeta('user-role') || 'guest';
    const staffRole = getMeta('staff-role') || '';
    const roomNumber = getMeta('room-number') || '';
    const userEmail = getMeta('user-email') || '';

    const channels = new Set(['announcements']);

    const effectiveRole = staffRole || role;

    if (['admin', 'super_admin', 'manager'].includes(effectiveRole)) {
      ['kitchen', 'front_desk', 'housekeeping', 'pos', 'maintenance', 'events'].forEach(c => channels.add(c));
    } else if (['kitchen', 'chef'].includes(effectiveRole)) {
      channels.add('kitchen');
      channels.add('pos');
    } else if (['front_desk'].includes(effectiveRole)) {
      channels.add('front_desk');
      channels.add('housekeeping');
      channels.add('pos');
    } else if (['housekeeping'].includes(effectiveRole)) {
      channels.add('housekeeping');
      channels.add('front_desk');
    } else if (['maintenance'].includes(effectiveRole)) {
      channels.add('maintenance');
    }

    if (roomNumber) {
      channels.add(`guest:${roomNumber}`);
    }
    if (userEmail) {
      channels.add(`guest:${userEmail}`);
    }

    return Array.from(channels);
  }

  function handleIncomingEvent(evtName, payload) {
    const channel = payload.channel || 'general';
    const data = payload.data || {};

    // 1. Dispatch custom DOM event for modular page hooks
    document.dispatchEvent(new CustomEvent(`sync:${channel}`, { detail: payload }));
    document.dispatchEvent(new CustomEvent('sync:event', { detail: payload }));

    // 2. High-priority toast notifications & screen hooks
    const notifyToast = typeof window.showToast === 'function' ? window.showToast : null;

    if (channel === 'kitchen' && evtName === 'new_order') {
      if (notifyToast) notifyToast(`🔔 Kitchen: New order #${data.order_no || ''} received!`, 'warning');
      if (window.location.pathname.includes('/kitchen')) {
        setTimeout(() => location.reload(), 1200);
      }
    } else if (channel === 'front_desk' && (evtName === 'room_cleaned' || evtName === 'room_unblocked')) {
      if (notifyToast) notifyToast(`✨ Room ${data.room_id || data.room_number || ''} is now clean & available.`, 'info');
      if (window.location.pathname.includes('/frontdesk') || window.location.pathname.includes('/rooms')) {
        const roomCard = document.querySelector(`[data-room-id="${data.room_id}"]`) || document.querySelector(`[data-room-number="${data.room_number}"]`);
        if (roomCard) {
          const badge = roomCard.querySelector('.badge-pill') || roomCard.querySelector('.badge');
          if (badge) {
            badge.className = 'badge-pill status-available';
            badge.textContent = 'Available';
          }
        }
      }
    } else if (channel === 'housekeeping' && evtName === 'room_updated') {
      if (window.location.pathname.includes('/housekeeping')) {
        setTimeout(() => location.reload(), 1500);
      }
    } else if (channel.startsWith('guest:') && evtName === 'order_status_updated') {
      if (notifyToast) notifyToast(`🍽️ Dining Order Status: ${data.status?.toUpperCase()}`, 'info');
      const orderBadge = document.getElementById(`order-status-${data.order_id}`);
      if (orderBadge) {
        orderBadge.textContent = data.status;
      }
    } else if (channel === 'announcements' && evtName === 'new_announcement') {
      if (notifyToast) notifyToast(`📢 ${data.title || 'New Announcement'}: ${data.message || ''}`, 'info');
      if (typeof window.loadLiveAnnouncements === 'function') {
        window.loadLiveAnnouncements();
      }
    }
  }

  function initSync() {
    if (typeof EventSource === 'undefined') {
      console.warn('SSE not supported in this browser.');
      return;
    }

    const channels = determineChannels();
    const streamUrl = `/api/sync/stream?channels=${encodeURIComponent(channels.join(','))}`;

    if (eventSource) {
      eventSource.close();
    }

    updateStatusIndicator('reconnecting');
    eventSource = new EventSource(streamUrl);

    eventSource.onopen = function () {
      reconnectAttempts = 0;
      updateStatusIndicator('connected');
      console.log('Real-Time Sync Stream connected to channels:', channels);
    };

    // Generic message listener
    eventSource.onmessage = function (e) {
      try {
        const payload = JSON.parse(e.data);
        handleIncomingEvent(payload.event || 'message', payload);
      } catch (err) {
        // Heartbeat ping or unformatted message
      }
    };

    // Named event listeners
    const knownEvents = ['new_order', 'order_status_updated', 'room_cleaned', 'room_updated', 'room_unblocked', 'new_announcement', 'ticket_created', 'ticket_updated'];
    knownEvents.forEach(evtName => {
      eventSource.addEventListener(evtName, function (e) {
        try {
          const payload = JSON.parse(e.data);
          handleIncomingEvent(evtName, payload);
        } catch (err) {
          console.warn('Error parsing sync event payload:', err);
        }
      });
    });

    eventSource.onerror = function () {
      updateStatusIndicator('reconnecting');
      eventSource.close();
      reconnectAttempts++;
      const delay = Math.min(1000 * Math.pow(2, reconnectAttempts - 1), maxReconnectDelay);
      console.warn(`Sync Stream disconnected. Reconnecting in ${delay / 1000}s... (Attempt ${reconnectAttempts})`);
      setTimeout(initSync, delay);
    };
  }

  document.addEventListener('DOMContentLoaded', () => {
    initSync();
  });
})();
