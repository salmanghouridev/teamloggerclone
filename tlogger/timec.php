<?php
/*
Plugin Name: User Time Logger
Description: Logs user time and displays it in a calendar format.
Version: 1.4
Author: Your Name
*/

// Activation hook to create database table
register_activation_hook(__FILE__, 'utl_create_table');

function utl_create_table() {
    global $wpdb;
    $table_name = $wpdb->prefix . 'user_time_logs';
    $charset_collate = $wpdb->get_charset_collate();

    $sql = "CREATE TABLE $table_name (
        id mediumint(9) NOT NULL AUTO_INCREMENT,
        user_id bigint(20) NOT NULL,
        project_name varchar(255) NOT NULL,
        task_name varchar(255) NOT NULL,
        start_time datetime NOT NULL,
        end_time datetime NOT NULL,
        duration varchar(20) NOT NULL,
        PRIMARY KEY (id)
    ) $charset_collate;";

    require_once(ABSPATH . 'wp-admin/includes/upgrade.php');
    dbDelta($sql);
}

// Add admin menu
add_action('admin_menu', 'utl_add_admin_menu');

function utl_add_admin_menu() {
    add_menu_page('User Time Logs', 'User Time Logs', 'manage_options', 'user-time-logs', 'utl_display_logs');
    add_submenu_page('user-time-logs', 'Screenshots', 'Screenshots', 'manage_options', 'user-screenshots', 'utl_display_screenshots');
}

// Display logs in the admin page
function utl_display_logs() {
    if (!current_user_can('manage_options')) {
        return;
    }

    global $wpdb;
    $table_name = $wpdb->prefix . 'user_time_logs';
    $current_user_id = get_current_user_id();
    
    $start_date = isset($_GET['start_date']) ? $_GET['start_date'] : '';
    $end_date = isset($_GET['end_date']) ? $_GET['end_date'] : '';
    $where_clause = $wpdb->prepare("WHERE user_id = %d", $current_user_id);
    
    if (!empty($start_date) && !empty($end_date)) {
        $where_clause .= $wpdb->prepare(" AND start_time BETWEEN %s AND %s", $start_date . ' 00:00:00', $end_date . ' 23:59:59');
    }

    $results = $wpdb->get_results("SELECT * FROM $table_name $where_clause ORDER BY start_time DESC");

    echo '<div class="wrap"><h1>User Time Logs</h1>';
    echo '<form method="GET">';
    echo '<input type="hidden" name="page" value="user-time-logs" />';
    echo 'Start Date: <input type="date" name="start_date" value="' . esc_attr($start_date) . '">';
    echo 'End Date: <input type="date" name="end_date" value="' . esc_attr($end_date) . '">';
    echo '<input type="submit" value="Filter">';
    echo '</form>';

    if ($results) {
        $total_duration_seconds = 0;
        $current_date = '';
        $daily_total_seconds = 0;

        echo '<table class="widefat fixed" cellspacing="0"><thead><tr><th>ID</th><th>User</th><th>Project</th><th>Task</th><th>Start Time</th><th>End Time</th><th>Duration</th></tr></thead><tbody>';
        foreach ($results as $row) {
            $user_info = get_userdata($row->user_id);
            $start_date = new DateTime($row->start_time);
            $end_date = new DateTime($row->end_time);
            $interval = $start_date->diff($end_date);
            $duration_seconds = $interval->h * 3600 + $interval->i * 60 + $interval->s;

            // Check if we are still in the same day
            if ($current_date !== $start_date->format('Y-m-d')) {
                if ($current_date !== '') {
                    echo '<tr style="background-color: #f1f1f1;"><td colspan="7"><strong>Total for ' . $current_date . ': ' . gmdate('H:i:s', $daily_total_seconds) . '</strong></td></tr>';
                }
                $current_date = $start_date->format('Y-m-d');
                $daily_total_seconds = 0;
            }
            $daily_total_seconds += $duration_seconds;
            $total_duration_seconds += $duration_seconds;

            echo '<tr>';
            echo '<td>' . esc_html($row->id) . '</td>';
            echo '<td>' . esc_html($user_info->user_login) . '</td>';
            echo '<td>' . esc_html($row->project_name) . '</td>';
            echo '<td>' . esc_html($row->task_name) . '</td>';
            echo '<td>' . esc_html($row->start_time) . '</td>';
            echo '<td>' . esc_html($row->end_time) . '</td>';
            echo '<td>' . esc_html($row->duration) . '</td>';
            echo '</tr>';
        }
        // Display the last daily total
        echo '<tr style="background-color: #f1f1f1;"><td colspan="7"><strong>Total for ' . $current_date . ': ' . gmdate('H:i:s', $daily_total_seconds) . '</strong></td></tr>';
        echo '</tbody></table>';

        // Display the grand total duration
        echo '<h2>Total Duration: ' . gmdate('H:i:s', $total_duration_seconds) . '</h2>';
    } else {
        echo '<p>No logs found.</p>';
    }

    echo '</div>';
}

// Display screenshots in the admin page
function utl_display_screenshots() {
    if (!current_user_can('manage_options')) {
        return;
    }

    $current_user_id = get_current_user_id();
    $attachments = get_posts(array(
        'post_type' => 'attachment',
        'posts_per_page' => -1,
        'author' => $current_user_id,
        'post_mime_type' => 'image',
        'orderby' => 'post_date',
        'order' => 'DESC',
    ));

    echo '<div class="wrap"><h1>User Screenshots</h1>';
    echo '<style>
        .screenshot-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 10px;
        }
        .screenshot-item {
            list-style: none;
        }
        .screenshot-item img {
            width: 100%;
            height: auto;
        }
        .screenshot-item p {
            text-align: center;
            margin: 5px 0;
        }
    </style>';

    if ($attachments) {
        echo '<ul class="screenshot-grid">';
        foreach ($attachments as $attachment) {
            $image_url = wp_get_attachment_url($attachment->ID);
            echo '<li class="screenshot-item">';
            echo '<a href="' . esc_url($image_url) . '" target="_blank">';
            echo wp_get_attachment_image($attachment->ID, 'thumbnail');
            echo '</a>';
            echo '<p>' . esc_html($attachment->post_title) . '</p>';
            echo '<p>' . esc_html(get_date_from_gmt($attachment->post_date, 'Y-m-d H:i:s')) . '</p>';
            echo '</li>';
        }
        echo '</ul>';
    } else {
        echo '<p>No screenshots found.</p>';
    }

    echo '</div>';
}

// Register REST API endpoints
add_action('rest_api_init', function () {
    register_rest_route('utl/v1', '/log', array(
        'methods' => 'POST',
        'callback' => 'utl_add_log_rest',
        'permission_callback' => function () {
            return is_user_logged_in();
        }
    ));
    
    register_rest_route('utl/v1', '/total', array(
        'methods' => 'GET',
        'callback' => 'utl_get_total_duration',
        'permission_callback' => function () {
            return is_user_logged_in();
        }
    ));
    
    register_rest_route('utl/v1', '/screenshots', array(
        'methods' => 'GET',
        'callback' => 'utl_get_user_screenshots',
        'permission_callback' => function () {
            return is_user_logged_in();
        }
    ));
    
    register_rest_route('utl/v1', '/user/(?P<username>[a-zA-Z0-9-]+)/combined', array(
        'methods' => 'GET',
        'callback' => 'utl_get_combined_data_by_username',
        'permission_callback' => function () {
            return true; // Allow public access
        }
    ));
});

function utl_add_log_rest(WP_REST_Request $request) {
    $user_id = get_current_user_id();
    $project_name = sanitize_text_field($request->get_param('project_name'));
    $task_name = sanitize_text_field($request->get_param('task_name'));
    $start_time = sanitize_text_field($request->get_param('start_time'));
    $end_time = sanitize_text_field($request->get_param('end_time'));
    $duration = sanitize_text_field($request->get_param('duration'));

    utl_add_log($user_id, $project_name, $task_name, $start_time, $end_time, $duration);

    return new WP_REST_Response('Log entry added', 200);
}

function utl_get_total_duration(WP_REST_Request $request) {
    global $wpdb;
    $table_name = $wpdb->prefix . 'user_time_logs';
    $user_id = get_current_user_id();
    
    $total_duration = $wpdb->get_var($wpdb->prepare(
        "SELECT SUM(TIMESTAMPDIFF(SECOND, start_time, end_time)) FROM $table_name WHERE user_id = %d",
        $user_id
    ));
    
    $hours = floor($total_duration / 3600);
    $minutes = floor(($total_duration % 3600) / 60);
    $seconds = $total_duration % 60;
    
    return new WP_REST_Response([
        'total_duration' => sprintf('%02d:%02d:%02d', $hours, $minutes, $seconds)
    ], 200);
}

// Function to add log entry to the database
function utl_add_log($user_id, $project_name, $task_name, $start_time, $end_time, $duration) {
    global $wpdb;
    $table_name = $wpdb->prefix . 'user_time_logs';
    $wpdb->insert(
        $table_name,
        array(
            'user_id' => $user_id,
            'project_name' => $project_name,
            'task_name' => $task_name,
            'start_time' => $start_time,
            'end_time' => $end_time,
            'duration' => $duration,
        )
    );
}

// Function to get user screenshots
function utl_get_user_screenshots(WP_REST_Request $request) {
    $current_user_id = get_current_user_id();

    $attachments = get_posts(array(
        'post_type' => 'attachment',
        'posts_per_page' => -1,
        'author' => $current_user_id,
        'post_mime_type' => 'image',
        'orderby' => 'post_date',
        'order' => 'DESC',
    ));

    $screenshots = array();
    foreach ($attachments as $attachment) {
        $screenshots[] = array(
            'id' => $attachment->ID,
            'url' => wp_get_attachment_url($attachment->ID),
            'title' => $attachment->post_title,
            'date' => $attachment->post_date,
        );
    }

    return new WP_REST_Response($screenshots, 200);
}

// Function to get combined data by username
function utl_get_combined_data_by_username(WP_REST_Request $request) {
    $username = $request->get_param('username');
    $user = get_user_by('login', $username);
    if (!$user) {
        return new WP_Error('no_user', 'User not found', array('status' => 404));
    }

    $user_id = $user->ID;
    
    // Fetch screenshots
    $screenshots = get_posts(array(
        'post_type' => 'attachment',
        'posts_per_page' => -1,
        'author' => $user_id,
        'post_mime_type' => 'image',
        'orderby' => 'post_date',
        'order' => 'DESC',
    ));

    $screenshots_data = array();
    foreach ($screenshots as $screenshot) {
        $screenshots_data[] = array(
            'id' => $screenshot->ID,
            'url' => wp_get_attachment_url($screenshot->ID),
            'title' => $screenshot->post_title,
            'date' => $screenshot->post_date,
        );
    }

    // Fetch time logs
    global $wpdb;
    $table_name = $wpdb->prefix . 'user_time_logs';
    $results = $wpdb->get_results($wpdb->prepare("SELECT * FROM $table_name WHERE user_id = %d ORDER BY start_time DESC", $user_id));

    return new WP_REST_Response([
        'time_logs' => $results,
        'screenshots' => $screenshots_data
    ], 200);
}
?>
