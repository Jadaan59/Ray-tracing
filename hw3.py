from helper_classes import *
import matplotlib.pyplot as plt

def render_scene(camera, ambient, lights, objects, screen_size, max_depth):
    width, height = screen_size
    ratio = float(width) / height
    screen = (-1, 1 / ratio, 1, -1 / ratio)  # left, top, right, bottom

    image = np.zeros((height, width, 3))

    for i, y in enumerate(np.linspace(screen[1], screen[3], height)):
        for j, x in enumerate(np.linspace(screen[0], screen[2], width)):
            # screen is on origin
            pixel = np.array([x, y, 0])
            origin = camera
            direction = normalize(pixel - origin)
            ray = Ray(origin, direction)

            # This is the main loop where **each pixel** color is computed.
            # Find intersection point and object.
            intersection = ray.nearest_intersected_object(objects)
            # If no intersection, we color the pixel black (no intersection = no light hitting the pixel = black)
            if intersection is None:
                color = np.zeros(3)
            # Otherwise, compute the color of intersection point
            else:
                color = get_color(ambient, lights, objects, max_depth, ray, intersection, 1)
            # We clip the values between 0 and 1 so all pixel values will make sense
            image[i, j] = np.clip(color, 0, 1)

    return image

# If the object is reflective, we recursively compute the color of the reflected ray.
# The depth of the recursion is limited by the max_depth parameter.
# The color is then added to the pixel color.
def get_color(ambient, lights, objects, max_depth, ray, intersection, depth):
    # The intersection information is a tuple containing the intersection point, the "t" and the object.
    intersection_point, intersection_t, min_obj = intersection
    # Get the normal at the intersection point
    normal = min_obj.get_normal(intersection_point)
    # To avoid self-intersection, we move the intersection point a little bit along the normal.
    intersection_point += normal * epsilon
    # The color of the pixel is initialized with 0
    color = np.zeros(3)
    # Next, we calculate Diffuse & Specular color
    # We only consider the lights that are not blocked by any object.
    unblocked_lights = [light for light in lights if light.is_unblocked(intersection_point, normal, objects)]
    if unblocked_lights:
        # For each unblocked light, we calculate the diffuse and specular color.
        sum_d_s_color_list = [light.sum_diffuse_specular_color(min_obj, intersection_point, normal, ray.direction) for light in unblocked_lights]
        # The color of the pixel is initialized with the ambient color, given the object's properties.
        color = min_obj.get_ambient_color(ambient)
        # We add the sum of the diffuse and specular colors to the pixel color.
        sum_d_s_color = np.sum(sum_d_s_color_list, axis=0)
        color += sum_d_s_color

    # If we reached the maximum depth, we return the pixel color.
    depth += 1
    if depth > max_depth:
        return color

    # If the object is reflective, recursively compute the color of the reflected ray
    if min_obj.reflection > 0:
        r_ray = construct_refracted_ray(ray, intersection_point, normal)
        r_intersection = r_ray.nearest_intersected_object(objects)
        if r_intersection is not None:
            r_color = get_color(ambient, lights, objects, max_depth, r_ray, r_intersection, depth)
            color += r_color * min_obj.reflection

    # If the object is refractive, recursively compute the color of the refracted ray
    if min_obj.refraction > 0:
        t_ray = construct_refracted_ray(ray, intersection_point, normal, min_obj.refractive_index)
        t_intersection = t_ray.nearest_intersected_object(objects)
        if t_intersection is not None:
            t_color = get_color(ambient, lights, objects, max_depth, t_ray, t_intersection, depth)
            color += t_color * min_obj.refraction

    return color





def your_own_scene():
    bubble_material = ([0.05, 0.05, 0.025], [0.05, 0.05, 0.025], [0.1, 0.1, 0.1], 100, 0.7, 0.9, 1.5)
    bubble_a = Sphere([-0.5, 0, -0.5],0.45)
    bubble_a.set_material(*bubble_material)
    bubble_b = Sphere([0.5, 0, -0.5],0.45)
    bubble_b.set_material(*bubble_material)
    plane_a = Plane([0,1,0],[0,-1,0])
    plane_a.set_material([0.7, 0.2, 0.35], [0.7, 0.2, 0.35], [1, 1, 1], 10, 0.5)
    plane_b = Plane([0,0,1], [0,0,-3])
    plane_b.set_material([0.7, 0.36, 0.38], [0.7, 0.36, 0.38], [1, 1, 1], 10, 0.5)

    objects = [bubble_a,bubble_b,plane_a,plane_b]

    # add the 2 lights sources
    p_light = PointLight(intensity= np.array([1, 1, 1]),position=np.array([0,1,1]),kc=0.1,kl=0.1,kq=0.1)
    d_light = DirectionalLight(intensity= np.array([1, 1, 0.56]),direction=np.array([1,1,1]))
    lights = [p_light, d_light]

    camera = np.array([0,0,1])
    return camera, lights, objects