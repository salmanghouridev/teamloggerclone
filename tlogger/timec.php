    <?php
    /*
    Plugin Name: User Time Logger
    Description: Logs user time and displays it in a calendar format.
    Version: 1.3
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

    // Register REST API endpoint
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
    add_action('rest_api_init', function () {
        register_rest_route('utl/v1', '/media', [
            'methods' => 'POST',
            'callback' => 'handle_screenshot_upload',
            'permission_callback' => function () {
                return current_user_can('edit_posts');
            }
        ]);
    });
    
    function handle_screenshot_upload(WP_REST_Request $request) {
        if (empty($_FILES['file']) || $_FILES['file']['error'] !== UPLOAD_ERR_OK) {
            return new WP_Error('upload_failed', 'Upload failed.', ['status' => 400]);
        }
    
        $uploaded_file = $_FILES['file'];
        $upload_overrides = ['test_form' => false];
        $movefile = wp_handle_upload($uploaded_file, $upload_overrides);
    
        if ($movefile && !isset($movefile['error'])) {
            $filename = $movefile['file'];
            $attachment = [
                'guid' => $movefile['url'],
                'post_mime_type' => $movefile['type'],
                'post_title' => sanitize_file_name(basename($filename)),
                'post_content' => '',
                'post_status' => 'inherit'
            ];
    
            $attach_id = wp_insert_attachment($attachment, $filename);
    
            require_once(ABSPATH . 'wp-admin/includes/image.php');
            $attach_data = wp_generate_attachment_metadata($attach_id, $filename);
            wp_update_attachment_metadata($attach_id, $attach_data);
    
            return new WP_REST_Response(['url' => $movefile['url']], 201);
        } else {
            return new WP_Error('upload_failed', $movefile['error'], ['status' => 500]);
        }
    }
    