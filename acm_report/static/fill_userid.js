'use strict';
(function() {
    $.getJSON("/user/autocomplete.json", function(users) {
        let ac_users = [];
        users.forEach(u => ac_users.push({ 
            value: u.category + '/' + u.name,
            data: u 
        }));
        $(".fill-user-id").each(function() {
            const input = $(this);

            const filters = input.data("fill-user-id-filter");
            const f_teacher = filters.indexOf('teacher') !== -1;
            const f_student = filters.indexOf('student') !== -1;
            const users = ac_users.filter(suggestion => {
                const data = suggestion.data;
                if (data.category === 'teacher') return f_teacher;
                return f_student;
            });

            const ac_options = {
                lookup: users,
                lookupFilter: function (suggestion, query, queryLowerCase) {
                    const data = suggestion.data;
                    if (data.initial.startsWith(queryLowerCase)) return true;
                    if (data.pinyin.replace(/ /g, '').startsWith(queryLowerCase)) return true;
                    if (data.stuid.startsWith(queryLowerCase)) return true;
                    if (data.name.startsWith(queryLowerCase)) return true;
                    return false;
                },
                onSelect: function (suggestion) {
                    const data = suggestion.data;
                    input.siblings(input.data("fill-user-id")).val(data.id);
                },
            };

            input.autocomplete(ac_options);
        })
    });
})();