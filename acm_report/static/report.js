'use strict';
(function() {
    const top_notification = $("#top-notification");

    $.getJSON("/user/autocomplete.json", function(users) {
        ac_users = [];
        users.forEach(u => ac_users.push({ value: u.category + '/' + u.name, data: u }));
        $(".fill-user-id").each(function() {
            const input = $(this);
            const ac_options = {
                lookup: ac_users,
                
                list: {
                    onSelectItemEvent: function() {
                        const id = input.getSelectedItemData().id;
                        input.siblings(input.data("fill-user-id")).val(id);
                    },
                }
            };

        })
    });

    $(document).ready(function() {

    });
})();