export const parseError = (error) => {
    if (error.response && error.response.data) {
        const data = error.response.data;
        
        if (data.non_field_errors) {
            return data.non_field_errors[0];
        } else if (error.response.status === 400 && Object.keys(data).length > 0) {
            const [key, value] = Object.entries(data)[0]
            return key + ': ' + value;
        }
    }
    return 'Unexpected error occured';
}
