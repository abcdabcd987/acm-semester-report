'use strict';
(function() {
    function update(table) {
        let checked = []
        let checkboxes = table.find('.table-helper-checkbox');
        let total = checkboxes.length;
        checkboxes.each(function(i, e) {
            e = $(e);
            let tr = e.closest('tr');
            if (e.prop('checked')) {
                checked.push(tr.data('value'));
                tr.addClass('info')
            } else {
                tr.removeClass('info');
            }
        });
        let toolbox = $(table.data('table-helper-toolbox'));
        toolbox.find('.table-helper-selected').val(checked.join('|'));
        toolbox.find('.table-helper-select-all').prop('checked', total === checked.length);
    }

    function gen_on_select_all_clicked(table) {
        return function on_select_all_clicked() {
            table.find('.table-helper-checkbox').prop('checked', this.checked);
            update(table);
        }
    }

    function on_row_clicked() {
        let tr = $(this);
        let checkbox = tr.find('.table-helper-checkbox');
        checkbox.prop('checked', !checkbox.prop('checked'));
        update(tr.closest('table'));
    }

    function on_checkbox_clicked(e) {
        event.stopPropagation();
        update($(this).closest('table'));
    }

    $(document).ready(function() {
        $('table.table-helper').each(function(i, table) {
            table = $(table);
            table.find('tbody tr').on('click', on_row_clicked);
            table.find('.table-helper-checkbox').on('click', on_checkbox_clicked);
            let toolbox = $(table.data('table-helper-toolbox'));
            toolbox.find('.table-helper-select-all').on('click', gen_on_select_all_clicked(table));
        })
    });
})();